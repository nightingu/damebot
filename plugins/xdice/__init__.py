import nonebot
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.typing import T_State
import asyncio
from nonebot.log import logger
from random import choice, randint
import re

nonebot.get_driver()
dice : Matcher = on_command('d', aliases={'r', 'roll'}, priority=100)

def start_end_alternative(first_start=True):
    if first_start:
        yield 0
    i = 1
    while True:
        yield from [-i, i]
        i += 1

async def summary(s: str, limit=50, keep_first=True, fill_in="などなど...\n"):
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
        return "".join(starts + [fill_in] + ends)
    else:
        return s
    


@dice.handle()
async def diceroll(bot: Bot, event: Event, state: T_State, matcher: Matcher):
    # get real command content
    logger.debug(f"event: {event}")
    logger.debug(f"state: {state}")
    command_text = event.get_message().extract_plain_text()
    logger.debug(f"got command text {command_text}")
    cmd = f"python -m roll {command_text}"
    logger.info(f"trying to execute {cmd}")
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    logger.debug(f"{cmd} process created.")
    stdout, stderr = await proc.communicate()
    logger.debug(f"got stdout \nf{stdout}")
    logger.debug(f"got stderr \nf{stderr}")
    if proc.returncode == 0:
    # also can use proc.returncode
        await matcher.finish(stdout.decode())
    else:
        err_short = await summary(stderr.decode())
        await matcher.finish(
f"""{choice(['ダメ', '駄目'])}{choice(['です', ''])}{"！" * randint(0,5)}
  {err_short}      
""")
