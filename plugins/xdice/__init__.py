from nonebot import on_command, CommandSession
from nonebot.matcher import Matcher
import asyncio
from nonebot.log import logger
from random import choice, randint

nonebot.get_driver()

dice : Matcher = on_command('d', aliases={'r', 'roll'}, priority=100)

@dice.handle()
async def diceroll(bot: Bot, event: Event, matcher: Matcher):
    # get real command content
    command_text = session.current_arg_text.strip()
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
