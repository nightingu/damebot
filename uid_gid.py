import asyncio
from nonebot.log import logger
import os
import re
import grp
import pwd
import subprocess

from json_store import JSONStore

async def execute_shell(cmd, cwd="/workspace"):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr

os.makedirs("/workspace/cache", exist_ok=True)

uid_map = JSONStore("/workspace/cache/uid_map.json", mode=0o644)
gid_map = JSONStore("/workspace/cache/gid_map.json", mode=0o644)

def ensure_group_sync(group_name="damebot"):
    gid_extra = f" -g {gid_map[group_name]}" if group_name in gid_map else ""
    cmd = f"groupadd -r{gid_extra} {group_name}"
    logger.debug(f"groupadd as '{cmd}'")
    code = os.system(cmd)
    success = code == 0 or code == 9
    if not success:
        logger.error(f"groupadd failed. ")
    else:
        gid_map[group_name] = grp.getgrnam(group_name).gr_gid
        gid_map.sync()
    return success
    # command = f'cat /etc/group | sed "s/:.*//" | grep {group_name}'

async def ensure_group(group_name="damebot"):
    gid_extra = f" -g {gid_map[group_name]}" if group_name in gid_map else ""
    cmd = f"groupadd -r{gid_extra} {group_name}"
    logger.debug(f"groupadd as '{cmd}'")
    code, out, err = await execute_shell(cmd)
    success = code == 0 or code == 9
    logger.debug(f"groupadd: {out, err}")
    if not success:
        logger.error(f"groupadd failed. {out, err}")
    else:
        gid_map[group_name] = grp.getgrnam(group_name).gr_gid
        gid_map.sync()
    return success
    # command = f'cat /etc/group | sed "s/:.*//" | grep {group_name}'

async def ensure_user(user_name, group_name="damebot"):
    logger.debug(f"ensuring user {user_name} and group {group_name} exists.")
    uid_extra = f" -u {uid_map[user_name]}" if user_name in uid_map else ""
    group_exist = await ensure_group(group_name)
    cmd = f"useradd -r {user_name}{uid_extra} -Ng {group_name}"
    logger.debug(f"useradd as '{cmd}'")
    code, out, err = await execute_shell(cmd)
    logger.debug(f"useradd: {out, err}")
    success = group_exist and (code == 0 or code == 9)
    if not success:
        logger.error(f"useradd failed. {out, err}")
    else:
        logger.debug(f"useradd: {out, err}")
        uid_map[user_name] = pwd.getpwnam(user_name).pw_uid
        uid_map.sync()
    return success

def init_workspace():
    ensure_group_sync("damebot")
    os.system("chmod 775 /workspace")
    os.system("chgrp damebot /workspace")

init_workspace()