import nonebot
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.typing import T_State
import asyncio
from nonebot.log import logger
from random import choice, randint
import re
import shlex

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
    
async def execute(cmd):
    logger.info(f"trying to execute '{cmd}'")
    proc = await asyncio.create_subprocess_exec(
        *shlex.split(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
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

class CommandBuilder:
    def __init__(self, cmd, *cmd_in_dice, help_short="--version", help_long="--help", sub_commands=None, priority=100, **kwargs):
        if not cmd_in_dice:
            cmd_in_dice = [cmd]
        if isinstance(help_short, str):
            help_short = execute(" ".join([cmd, help_short]))
        if isinstance(help_long, str):
            help_long = execute(" ".join([cmd, help_long]))
        if sub_commands is None:
            sub_commands = []
        self.cmd = cmd
        self.cmd_in_dice = cmd_in_dice
        self.help_short = help_short
        self.help_long = help_long
        self.sub_commands = sub_commands
        self.priority = priority
        self.extra_kwargs = kwargs

    def build(self) -> Matcher:
        main_command, *aliases = [x + " " for x in self.cmd_in_dice]
        aliases = set(aliases)
        matcher = on_command(main_command, aliases=aliases, priority=self.priority, **self.extra_kwargs)
        @matcher.handle()
        async def cmd_handler(bot: Bot, event: Event, state: T_State, matcher: Matcher):
            # get real command content
            logger.debug(f"event: {event}")
            logger.debug(f"state: {state}")
            command_text = event.get_message().extract_plain_text().strip()
            logger.debug(f"got command text '{command_text}'")
            cmd = " ".join([self.cmd, command_text])
            output = await execute(cmd)
            await matcher.send(output)
        matcher.command_builder = self
        return matcher



    