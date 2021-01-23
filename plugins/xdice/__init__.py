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
damebot help: if you see ダメ/駄目, there must be something wrong.
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

# async def identity(x):
#     return x

# async def wait_lazy_dict(d: dict):
#     keys = d.keys()
#     values = await asyncio.gather(*d.values())
#     return {k:v for k,v in zip(keys, values)}

# helper : Matcher = on_command('h', aliases={'help'}, priority=50)
# @helper.handle()
# async def help(bot: Bot, event: Event, state: T_State, matcher: Matcher):
#     # get real command content
#     logger.debug(f"event: {event}")
#     logger.debug(f"state: {state}")
#     command_text = event.get_message().extract_plain_text().strip()
#     logger.debug(f"got command text '{command_text}'")
#     # TODO: change to plugin.matcher for plugin in nonebot.get_loaded_plugins() 
#     if command_text == "":
#         help_table = {
#             "d(r/roll)": execute(f"python -m roll --version d"),
#             "h(help)": identity("help for damebot.")
#         }
#         help_table = await wait_lazy_dict(help_table)
#         output = "\n".join(f"{k}:{v.strip()}" for k,v in help_table.items())
#     elif command_text in {"d", "r", "roll"}:
#         output = await execute("python -m roll --help")
#     else:
#         output = dame(f"No help for '{command_text}'")
#     await matcher.finish(output)
