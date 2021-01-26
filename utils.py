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
    return f"""{choice(['ダメ', '駄目'])}{choice(['です', ''])}{"！" * randint(0,5)}
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
    
def as_script(cmd_script: str, bash_cache="cache", cwd="/workspace"):
    md5 = hashlib.md5(cmd_script.encode("utf-8"))
    os.makedirs(os.path.join(cwd, bash_cache), exist_ok=True)
    full_path = os.path.join(cwd, bash_cache, f"{md5.hexdigest()}.sh")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(cmd_script)
    os.system(f"chmod 700 {full_path}")
    return f"{full_path}"

async def execute_shell(cmd, cwd="/workspace"):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr

async def ensure_group(group_name="damebot"):
    code, out, err = await execute_shell(f"groupadd {group_name}")
    success = code == 0 or code == 9
    logger.debug(f"groupadd: {out, err}")
    if not success:
        logger.error(f"groupadd failed. {out, err}")
    return success
    # command = f'cat /etc/group | sed "s/:.*//" | grep {group_name}'

async def ensure_user(user_name, group_name="damebot"):
    logger.debug(f"ensuring user {user_name} and group {group_name} exists.")
    group_exist = await ensure_group(group_name)
    code, out, err = await execute_shell(f"useradd {user_name} -G {group_name}")
    logger.debug(f"useradd: {out, err}")
    success = group_exist and (code == 0 or code == 9)
    if not success:
        logger.error(f"useradd failed. {out, err}")
    return success


def set_ids(user_name):
    def _set_id():
        user = pwd.getpwnam(user_name)
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)
    return _set_id

async def execute(cmd, cwd="/workspace", user="commander"):
    result = await ensure_user(user)
    splited = shlex.split(cmd)
    logger.info(f"trying to execute {splited}")
    proc = await asyncio.create_subprocess_exec(
        *splited,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        preexec_fn=set_ids(user)
    )
    logger.debug(f"'{cmd}' process created.")
    stdout, stderr = await proc.communicate()
    logger.debug(f"got stdout \nf{stdout}")
    logger.debug(f"got stderr \nf{stderr}")
    if proc.returncode == 0:
    # also can use proc.returncode
        output = stdout.decode()
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

import inspect
class CommandBuilder:
    def __init__(
        self, cmd, 
        *cmd_in_dice, 
        help_short="--version", 
        help_short_text=None, 
        help_long="--help", 
        help_long_text=None, 
        help_async_factory=None, 
        help_short_async_factory=None, 
        help_long_async_factory=None, 
        sub_commands=None, 
        priority=65536, 
        **extra_kwargs):
        _locals = locals()
        _spec = inspect.getfullargspec(self.__init__)
        _args = [_locals[x] for x in _spec.args] + list(_locals[_spec.varargs])
        _kwargs = {x:_locals[x] for x in _spec.kwonlyargs}
        _kwargs.update(_locals[_spec.varkw])
        if sub_commands is None:
            sub_commands = []
        # else:
        #     if isinstance(sub_commands, (str, CommandBuilder, dict)):
        #         sub_commands = [sub_commands]
        #     new_sub_commands = []
        #     for sub_command in sub_commands:
        #         if isinstance(sub_command, str):
        #             sub = sub_command
        #             args = [" ".join([x, sub]) for x in _args]
        #             kwargs = _kwargs.copy()
        #             kwargs["sub_commands"] = None
        #             sub_command = CommandBuilder(*args, **kwargs)
        #         elif isinstance(sub_command, dict):
        #             sub_dict_commands = []
        #             for sub, subsub in sub_command.items():
        #                 args = [" ".join([x, sub_command]) for x in _args]
        #                 kwargs = _kwargs.copy()
        #                 kwargs["sub_commands"] = subsub
        #                 sub_dict_commands.append(CommandBuilder(*args, **kwargs))
        #             sub_command = sub_dict_commands
        #         new_sub_commands.append(sub_command)
        #     sub_commands = new_sub_commands
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
        self.cmd = cmd
        self.cmd_in_dice = cmd_in_dice
        self.help_short = help_short
        self.help_long = help_long
        self.help_short_async_factory = help_short_async_factory
        self.help_long_async_factory = help_long_async_factory
        self.sub_commands = sub_commands
        self.priority = priority
        self.extra_kwargs = extra_kwargs

    def build_help(self, *help_prefixes, priority=None, recursive=True, **help_args):
        logger.info(f"building help for '{self.cmd}' using '{self.help_short_async_factory.__name__}:{self.help_short}' and '{self.help_long_async_factory.__name__}:{self.help_long}'")
        if priority is None:
            priority = self.priority // 2
        if len(help_prefixes) == 0:
            help_prefixes = ["help"]
        all_commands_combined = [help_name + ("" if self.cmd is None else f" {self_name}") for self_name in self.cmd_in_dice for help_name in help_prefixes]
        main_command, *aliases = all_commands_combined
        aliases = set(aliases)
        sub_matchers = None
        if recursive:
            sub_matchers = [child_cmd.build_help(*help_prefixes, priority=priority-1, recursive=recursive, **help_args) for child_cmd in self.sub_commands]        
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
{newline.join(f'{k}:{v.strip()}' for k,v in zip(
    ('|'.join(comm.cmd_in_dice) for comm in self.sub_commands), 
    sub_commands_texts
    )
).strip()}
""".strip()
            await matcher.finish(output)
        logger.info(f"builded help")
        return (matcher, sub_matchers) if sub_matchers else matcher     

    def build(self, build_sub=True, recursive=False) -> Matcher:
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
                output = await execute(cmd)
                await matcher.send(output)
            matcher.command_builder = self
        matcher_subs = [x.build(build_sub=recursive, recursive=recursive) for x in self.sub_commands] if build_sub else None
        logger.info(f"builded '{self.cmd}'")
        for item in [matcher, matcher_subs]:
            if item is not None:
                return item

