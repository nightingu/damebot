from nonebot import on_command, CommandSession
import asyncio

@on_command('d', aliases=('dice', '骰', 'roll'))
async def diceroll(session: CommandSession):
    # get real command content
    command_text = session.current_arg_text.strip()
    cmd = f"roll {command_text}"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    # also can use proc.returncode
    await session.send(stdout.decode())
