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
from utils import *
from collections import namedtuple



nonebot.get_driver()

root = CommandBuilder(
    None, 
    help_long_text="""
help|h: damebot! if you see ダメ/駄目, there must be something wrong.
""",
    sub_commands=[
        CommandBuilder(
            "python -m roll", 
            "r", "d", "roll",
            help_short="--version d",
        ),
        CommandBuilder("ls", help_short_text="Linux命令 ls"),
        CommandBuilder("pwd", help_short_text="Linux命令 pwd"),
        CommandBuilder("cat", help_short_text="Linux命令 cat"),
        CommandBuilder("base64", help_short_text="Linux命令 base64"),
        CommandBuilder(as_script('echo "$2" > $1'), "write", run_as="dameuser", help_short_text="write files like 'echo $2 > $1'. ", help_long_text="Usage: write <file_name> 'text'"),
        CommandBuilder("sed", help_short_text="Linux命令 sed"),
        CommandBuilder("whoami", help_short_text="Linux命令 whoami"),
    ]
)
root.build()
root.build_help("h", "help")
