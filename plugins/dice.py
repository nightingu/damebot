from nonebot import on_command, CommandSession
import asyncio
import logging

@on_command('d', aliases=('dice', '骰', 'roll'))
async def diceroll(session: CommandSession):
    # get real command content
    command_text = session.current_arg_text.strip()
    cmd = f"roll {command_text}"
    logging.info(f"trying to execute {cmd}")
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    logging.info(f"{cmd} process created.")
    stdout, stderr = await proc.communicate()
    logging.info(f"got stdout \nf{stdout}")
    logging.info(f"got stderr \nf{stderr}")

    # also can use proc.returncode
    await session.send(stdout.decode())
