import nonebot
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.typing import T_State
import asyncio
from nonebot.log import logger
from random import choice, randint

nonebot.get_driver()
dice : Matcher = on_command('d', aliases={'r', 'roll'}, priority=100)

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
        await matcher.finish(
f"""{choice(['ダメ', '駄目'])}{choice(['です', ''])}{"！" * randint(0,5)}
  {stderr.decode()}      
""")
