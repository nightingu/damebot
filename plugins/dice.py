from nonebot import on_command, CommandSession
import asyncio
from nonebot.log import logger

@on_command('d', aliases=('dice', '骰', 'roll'))
async def diceroll(session: CommandSession):
    # get real command content
    command_text = session.current_arg_text.strip()
    cmd = f"roll {command_text}"
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

    # also can use proc.returncode
    await session.send(stdout.decode())
