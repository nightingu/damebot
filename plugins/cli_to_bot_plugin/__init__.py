from datetime import date, time
import json
from pprint import pformat
import nonebot
from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher
from nonebot.plugin import on, on_message
from nonebot.rule import Rule
from nonebot.typing import T_State
import asyncio
from nonebot.log import logger
from random import choice, randint
import re
import shlex
from utils import *
from workspace import *
from collections import namedtuple
import pathlib
import docopt
from nonebot.adapters.cqhttp import PokeNotifyEvent
from scripts import download

nonebot.get_driver()
logger.add(LOGS / "command_log.log", rotation="1 day", filter=__name__)
logger.add(LOGS / "running_log.log", rotation="1 day")

async def download_env(bot: Bot, event: Event, state: T_State, matcher: Matcher, regex: str):
    envs = await command_env_settings(bot, event, state, matcher, regex)
    if "BOT_GROUP_ID" not in envs:
        raise ValueError(f"not in group, no group files found")
    group_id = int(envs["BOT_GROUP_ID"])
    try:
        args = docopt.docopt(download.__doc__, shlex.split(envs["BOT_EVENT_COMMAND_ARGS"]), help=False)
    except docopt.DocoptExit as e:
        raise ValueError(e)
    file_name = args["<path>"] or args["<tar_or_zip>"]
    file_path = pathlib.Path(file_name)
    current_files = await bot.call_api("get_group_root_files", group_id=group_id)
    for folder_path in file_path.parts[:-1]:
        folders = current_files["folders"]
        folder_map = {folder["folder_name"]:folder for folder in folders}
        current_files = await bot.call_api("get_group_files_by_folder", group_id=group_id, folder_id=folder_map[folder_path]["folder_id"])
    file_map = {file["file_name"]:file for file in current_files["files"]}
    file_item = file_map[file_path.parts[-1]]
    file_url = await bot.call_api("get_group_file_url", group_id=group_id, file_id=file_item["file_id"], busid=file_item["busid"])
    envs["BOT_DOWNLOAD_URL"] = file_url["url"]
    return envs

root = CommandBuilder(
    None, 
    help_long_text="""
help|h: damebot! if you see だめ/ダメ/駄目, there must be something wrong.
""",
    sub_commands=[
        CommandBuilder(
            "python -m roll", 
            "roll", "r",
            help_short="--version d",
        ),
        CommandBuilder(
            "python -m roll", 
            "rollhidden", "rh",
            help_short="暗骰dice",
            hidden_result=True,
        ),
        CommandBuilder(
            script(PROJECT_SCRIPT / "mylist.py"), 
            "list", "l",
            per_group=True,
            workespace_mode=WorkspaceMode.plaintext,
        ),
        CommandBuilder(
            script(PROJECT_SCRIPT / "no_bash.py"),
            "bash", "!",
            workespace_mode=WorkspaceMode.none,
            per_group=True,
        ),
        CommandBuilder(
            script(PROJECT_SCRIPT / "download.py"), 
            "download",
            priority_delta=-1, 
            per_group=True,
            command_env_async_factory=download_env
        ),
        CommandBuilder(
            script(PROJECT_SCRIPT / "haiku.py"), 
            "paiju", "pj",
            priority_delta=-1, 
            per_group=False,
            workespace_mode=WorkspaceMode.serial,
        ),
        CommandBuilder(
            script(PROJECT_SCRIPT / "nyan.py"), 
            "nyan", "miao", "m",
            priority_delta=-1, 
            per_group=False,
            workespace_mode=WorkspaceMode.serial,
        )
    ]
)

def has_message(event):
    try:
        event.get_plaintext()
        return True
    except ValueError:
        return False

root.build()
root.build_help("h", "help")
async def loggable(bot: "Bot", event: "Event", state: T_State):
    return event.is_tome() \
        or (has_message(event) and any(event.get_plaintext().startswith(x) for x in nonebot.get_driver().config.command_start)) \
        # or getattr(event, "sub_type", None) == "poke" \
        # or isinstance(event, PokeNotifyEvent) \


memo = on(rule=Rule(loggable), priority=64, block=False)

def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, date):
        serial = obj.isoformat()
        return serial

    if isinstance(obj, time):
        serial = obj.isoformat()
        return serial

    return obj.__dict__

@memo.handle()
async def user_group_memo(bot: "Bot", event: "Event", state: T_State):
    new_group_id = getattr(event, "group_id", None)
    logger.info("{}", json.dumps(event, default=serialize))
    if new_group_id is not None:
        user_group_map.set(str(event.user_id), new_group_id)
