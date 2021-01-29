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
from workspace import *
from collections import namedtuple
import pathlib

nonebot.get_driver()

async def download_env(bot: Bot, event: Event, state: T_State, matcher: Matcher, regex: str):
    envs = await command_env_settings(bot, event, state, matcher, regex)
    if "BOT_GROUP_ID" not in envs:
        raise ValueError(f"not in group, no group files found")
    group_id = int(envs["BOT_GROUP_ID"])
    file_name = envs["BOT_EVENT_COMMAND_ARGS"].strip()
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
        )
    ]
)
root.build()
root.build_help("h", "help")
