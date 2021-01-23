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
    ]
)
root.build()
root.build_help("h", "help")
