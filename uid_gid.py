import asyncio
from nonebot.log import logger
import os
import re
import grp
import pwd
import subprocess
from workspace import *
import workspace

from json_store import JSONStore

async def execute_shell(cmd, cwd=WORKSPACE):
    logger.debug(f"'{cmd}'")
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await proc.communicate()
    logger.debug(f"usermod[{proc.returncode}] {stdout, stderr}")
    return proc.returncode, stdout, stderr

uid_map = JSONStore(CACHE / "uid_map.json", mode=0o644)
gid_map = JSONStore(CACHE / "gid_map.json", mode=0o644)
user_main_group = JSONStore(CACHE / "user_group.json", mode=0o644)
user_extra_group = JSONStore(CACHE / "user_extra_group.json", mode=0o644)

def ensure_group_sync(group_name="damebot"):
    return asyncio.run(ensure_group(group_name))

async def ensure_group(group_name="damebot"):
    gid_extra = f" -g {gid_map[group_name]}" if group_name in gid_map else ""
    cmd = f"groupadd -r{gid_extra} {group_name}"
    code, out, err = await execute_shell(cmd)
    success = code == 0 or code == 9
    if not success:
        logger.error(f"groupadd failed. {out, err}")
    else:
        logger.debug(f"groupadd succeed. {out, err}")
        gid_map[group_name] = grp.getgrnam(group_name).gr_gid
        gid_map.sync()
    return success
    # command = f'cat /etc/group | sed "s/:.*//" | grep {group_name}'

async def ensure_user(user_name, group_name="damebot", extra_group=tuple()):
# def ensure_user_sync(user_name, group_name="damebot", extra_group=tuple()):
    logger.debug(f"ensuring user {user_name} and group {group_name} {extra_group} exists.")
    uid_extra = f" -u {uid_map[user_name]}" if user_name in uid_map else ""
    group_exist = await ensure_group(group_name)
    extra_group_values = await asyncio.gather(*(ensure_group(group) for group in extra_group))
    extra_group_exists = all(extra_group_values)
    group_all_exists = group_exist and extra_group_exists
    cmd = f"useradd -r {user_name}{uid_extra} -Ng {group_name}"
    code, out, err = await execute_shell(cmd)
    success = group_all_exists and (code == 0 or code == 9)
    for group in extra_group:
        cmd_usermod = f"usermod {user_name} -aG {group}"
        code, out, err = await execute_shell(cmd_usermod)
        success = success and (code == 0 or code == 9)
    if not success:
        logger.error(f"useradd failed. ")
    else:
        logger.debug(f"useradd succeed.")
        uid_map[user_name] = pwd.getpwnam(user_name).pw_uid
        uid_map.sync()
        gid_reverse = {v:k for k,v in gid_map.items()}
        main_group_name = gid_reverse[pwd.getpwnam(user_name).pw_gid]
        logger.debug(f"group {main_group_name} for {user_name}")
        user_main_group[user_name] = main_group_name
        groups = [g.gr_name for g in grp.getgrall() if user_name in g.gr_mem]
        logger.debug(f"groups {groups} for {user_name}")
        if main_group_name in groups:
            groups.remove(main_group_name)
        user_extra_group[user_name] = groups
        user_main_group.sync()
        user_extra_group.sync()
    return success
   
def ensure_user_sync(user_name, group_name="damebot", extra_group=tuple()):
    return asyncio.run(ensure_user(user_name, group_name, extra_group))
    
default_group = "damebot"

def ensure_shared_dir(path: Path): 
    os.makedirs(path, exist_ok=True)
    os.system(f"chgrp {default_group} {path}")
    os.system(f"chmod g+w {path}")
    os.system(f"chmod +t {path}") 

def ensure_user_dir(path: Path, user: str): 
    os.makedirs(path, exist_ok=True)
    os.system(f"chown {user} {path}")

def init_workspace():
    logger.debug(f"init default group {default_group}")
    ensure_group_sync(default_group)
    for group in gid_map:
        logger.debug(f"init group {group}")
        ensure_group_sync(group)
    for user in uid_map:  
        logger.debug(f"init user {user}")
        ensure_user_sync(user, user_main_group.get(user, default_group), user_extra_group.get(user, []))
    for item in workspace.__dict__.values():
        if isinstance(item, Path):
            os.makedirs(item, exist_ok=True)
            os.system(f"chmod 755 {item}")
            os.system(f"chgrp root {item}")
            os.system(f"chown root {item}")
    ensure_shared_dir(SHARED)
