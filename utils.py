import shutil
from tokenize import group
from typing import Dict
import nonebot
from nonebot import on_command, on_regex
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.typing import T_State
import asyncio
from nonebot.log import logger
from random import choice, randint
import os
import re
import shlex
import hashlib
import grp
import pwd
from uid_gid import ensure_user


def start_end_alternative(first_start=True):
    if first_start:
        yield 0
    i = 1
    while True:
        yield from [-i, i]
        i += 1

def fill_in_generate():
    return "\n" + choice(["いぉ","など"]) * randint(2,3) + "." * randint(3,6) + "\n"

def dame(err: str):
    return f"""{choice(['だめ', 'ダメ', '駄目'])}{choice(['です', ''])}{"！" * randint(0,5)}
  {err}      
""".strip()

async def summary(s: str, limit=50, keep_first=True, fill_in_gen=fill_in_generate):
    if len(s) > limit:
        lines = s.splitlines(keepends=True)
        if len(lines) <= 1:
            words = [x + " " for x in s.split()]
            if len(words) <= 1:
                chinese_phrases = re.split("|".join(f"(?<={x})" for x in ["，","。","；"]), s)
                units = chinese_phrases
            else:
                units = words
        else:
            units = lines
        starts = []
        ends = []
        collected_counts = 0
        for i in start_end_alternative(keep_first):
            current = starts if i >= 0 else ends
            unit = units[i]
            current.append(unit)
            collected_counts += len(unit)
            if collected_counts > limit:
                break
        ends.reverse()
        return ("".join(starts) + fill_in_gen() + "".join(ends)).strip()
    else:
        return s
    
# def as_script(cmd_script: str, bash_cache="cache", cwd="/workspace"):
#     md5 = hashlib.md5(cmd_script.encode("utf-8"))
#     os.makedirs(os.path.join(cwd, bash_cache), exist_ok=True)
#     full_path = os.path.join(cwd, bash_cache, f"{md5.hexdigest()}.sh")
#     with open(full_path, "w", encoding="utf-8") as f:
#         f.write(cmd_script)
#     os.system(f"chmod 755 {full_path}")
#     return f"{full_path}"

def script(cmd: str, bash_cache="cache", cwd="/workspace"):
    target_path = os.path.join(cwd, bash_cache)
    _, file_name = os.path.split(cmd)
    full_path = os.path.join(cwd, bash_cache, file_name)
    shutil.copy(cmd, full_path)
    os.system(f"chmod 755 {full_path}")
    return f"{full_path}"

def set_ids(user_name):
    def _set_id():
        user = pwd.getpwnam(user_name)
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)
    return _set_id

async def execute(cmd, cwd="/workspace", user="commander", env_vars=None):
    if env_vars is None:
        env_vars = {}
    result = await ensure_user(user)
    splited = shlex.split(cmd)
    logger.info(f"trying to execute {splited}")
    proc = await asyncio.create_subprocess_exec(
        *splited,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        preexec_fn=set_ids(user),
        env=env_vars,
    )
    logger.debug(f"'{cmd}' process created.")
    stdout, stderr = await proc.communicate()
    logger.debug(f"got stdout \nf{stdout}")
    logger.debug(f"got stderr \nf{stderr}")
    if proc.returncode == 0:
    # also can use proc.returncode
        output = stdout.decode()
        if output.strip() == "":
            output = stderr.decode()
            if output.strip() == "":
                output = f"'{cmd}' できだ" + "！" * randint(1,3)
    else:
        err_short = await summary(stderr.decode())
        output = dame(err_short)
    return output

async def multi_execute(cmd, user_typed_cmd, help_obj):
    logger.debug("using execute help producer")
    result = await execute(" ".join([cmd, user_typed_cmd, help_obj]))
    return result

async def plain_string(cmd, user_typed_cmd, help_obj):
    logger.debug("using plain_string help producer")
    return help_obj

async def command_env_settings(bot: Bot, event: Event, state: T_State, matcher: Matcher, regex: str):
    env_vars = os.environ.copy()
    env_vars["BOT_EVENT_TYPE"] = str(event.get_type())
    msg = str(event.get_plaintext())
    env_vars["BOT_EVENT_MESSAGE"] = msg
    _, origin_command, command_text = re.match(regex, msg, flags=re.MULTILINE | re.DOTALL).groups()
    env_vars["BOT_EVENT_COMMAND"] = origin_command
    env_vars["BOT_EVENT_COMMAND_ARGS"] = command_text
    group_id = getattr(event, "group_id", None)
    if group_id is not None:
        env_vars["BOT_GROUP_ID"] = str(group_id)
    env_vars["BOT_USER_ID"] = str(event.get_user_id())
    env_vars["BOT_SESSION_ID"] = str(event.get_session_id())
    if event.is_tome():
        env_vars["TO_BOT"] = str(1)
    return env_vars

def nop():
    pass

class CommandBuilder:
    def __init__(
        self, cmd, 
        *cmd_in_dice, 
        run_as="user",
        help_short="--version", 
        help_short_text=None, 
        help_long="--help", 
        help_long_text=None, 
        help_async_factory=None, 
        help_short_async_factory=None, 
        help_long_async_factory=None, 
        sub_commands=None, 
        priority=65536, 
        priority_delta=0,
        help_priority=65536 // 2, 
        help_priority_delta=0,
        init_fn=None,
        command_env_async_factory=command_env_settings,
        **extra_kwargs):
        if sub_commands is None:
            sub_commands = []
        if len(cmd_in_dice) == 0:
            cmd_in_dice = [cmd]
        if help_async_factory is None:
            help_async_factory = multi_execute
        if help_short_async_factory is None:
            help_short_async_factory = help_async_factory if help_short_text is None else plain_string
        if help_long_async_factory is None:
            help_long_async_factory = help_async_factory if help_long_text is None else plain_string  
        if help_short_text is not None:
            help_short = help_short_text
        if help_long_text is not None:
            help_long = help_long_text
        if init_fn is None:
            init_fn = nop
        self.cmd = cmd
        self.init_fn = init_fn
        self.run_as = run_as
        self.cmd_in_dice = cmd_in_dice
        self.help_short = help_short
        self.help_long = help_long
        self.help_short_async_factory = help_short_async_factory
        self.help_long_async_factory = help_long_async_factory
        self.sub_commands = sub_commands
        self.priority = priority + priority_delta
        self.help_priority = help_priority + help_priority_delta
        self.extra_kwargs = extra_kwargs
        self.command_env_async_factory = command_env_async_factory

    def build_help(self, *help_prefixes, priority_delta=0, recursive=True, **help_args):
        logger.info(f"building help for '{self.cmd}' using '{self.help_short_async_factory.__name__}:{self.help_short}' and '{self.help_long_async_factory.__name__}:{self.help_long}'")
        priority = self.help_priority + priority_delta
        if len(help_prefixes) == 0:
            help_prefixes = ["help"]
        all_commands_combined = [help_name + ("" if self.cmd is None else f" {self_name}") for self_name in self.cmd_in_dice for help_name in help_prefixes]
        main_command, *aliases = all_commands_combined
        aliases = set(aliases)
        sub_matchers = None
        if recursive:
            sub_matchers = [child_cmd.build_help(*help_prefixes, priority_delta=priority_delta-1, recursive=recursive, **help_args) for child_cmd in self.sub_commands]        
        config = nonebot.get_driver().config
        command_start = config.command_start
        regex = f"^({'|'.join(command_start)})({'|'.join(all_commands_combined)})(.*)$"
        logger.info(f"building command help matcher with {regex}, prior={priority}, kwargs={help_args}")
        matcher = on_regex(regex, flags=re.MULTILINE, block=True, priority=priority, **help_args)
        @matcher.handle()
        async def help(bot: Bot, event: Event, state: T_State, matcher: Matcher):
            # get real command content
            logger.debug(f"event: {event}")
            logger.debug(f"state: {state}")
            msg = event.get_message().extract_plain_text()
            logger.debug(f"got message '{msg}'")
            _, origin_command, command_text = re.match(regex, msg, flags=re.MULTILINE).groups()
            logger.debug(f"got command text '{command_text}'")
            extra_prompt = ""
            if not command_text.startswith(" ") and command_text != "":
                extra_prompt += f"treat '{origin_command + command_text}' as '{origin_command}'\n"
                logger.warning(extra_prompt)
                command_text = ""
            else:
                command_text = command_text.strip()
            command_without_help = origin_command.split()[-1]
            logger.debug(f"{command_without_help} => {self.cmd}")
            logger.debug(f"planning to call with '{self.cmd}', '{command_text}', '{self.help_long}'")
            help_long_text = await self.help_long_async_factory(self.cmd, command_text, self.help_long)
            
            sub_commands_texts = await asyncio.gather(*[command.help_short_async_factory(command.cmd, command_text, command.help_short) for command in self.sub_commands])
            newline = '\n'
            output = \
f"""
{extra_prompt}{help_long_text.strip()}

sub-commands:
{newline.join(f'{k}[{u}]:{v.strip()}' for k,u,v in zip(
    ('|'.join(comm.cmd_in_dice) for comm in self.sub_commands), 
    (f'{comm.run_as}' for comm in self.sub_commands), 
    sub_commands_texts
    )
).strip()}
""".strip()
            await matcher.finish(output)
        logger.info(f"builded help")
        return (matcher, sub_matchers) if sub_matchers else matcher     

    def build(self, build_sub=True, recursive=False) -> Matcher:
        self.init_fn()
        logger.info(f"building '{self.cmd}'")
        if recursive:
            build_sub = True
        matcher = None
        if self.cmd is not None:
            config = nonebot.get_driver().config
            command_start = config.command_start
            regex = f"^({'|'.join(command_start)})({'|'.join(self.cmd_in_dice)})(.*)$"
            matcher = on_regex(regex, flags=re.MULTILINE, block=True, priority=self.priority, **self.extra_kwargs)
            logger.info(f"building command matcher with '{regex}', prior={self.priority}, kwargs={self.extra_kwargs}")
            @matcher.handle()
            async def cmd_handler(bot: Bot, event: Event, state: T_State, matcher: Matcher):
                # get real command content
                logger.debug(f"event: {event}")
                logger.debug(f"state: {state}")
                msg = event.get_message().extract_plain_text()
                logger.debug(f"got message '{msg}'")
                _, origin_command, command_text = re.match(regex, msg, flags=re.MULTILINE | re.DOTALL).groups()
                command_text = command_text.strip()
                logger.debug(f"got command text '{command_text}'")
                cmd = " ".join([self.cmd, command_text])
                env_futures = await asyncio.gather(self.command_env_async_factory(bot, event, state, matcher, regex), return_exceptions=True)
                env_vars = env_futures[0]
                if isinstance(env_vars, Exception):
                    await matcher.send(dame(str(env_vars)))
                    raise env_vars
                output = await execute(cmd, user=self.run_as, env_vars=env_vars)
                await matcher.send(output)
            matcher.command_builder = self
        matcher_subs = [x.build(build_sub=recursive, recursive=recursive) for x in self.sub_commands] if build_sub else None
        logger.info(f"builded '{self.cmd}'")
        for item in [matcher, matcher_subs]:
            if item is not None:
                return item

