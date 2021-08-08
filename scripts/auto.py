#!/usr/local/bin/python

properties = "type|extract|template|survival|period"
properties_actions = "clear|set|add"
module_actions = "create|status|remove|on|off"

f"""用于控制自动回复，生成自动回复用命令，以及管理自动回复模板，自动回复条件。
你可以在其中添加支持的其他命令来使得机器人自动工作。

Usage:
  auto ({module_actions}) all [permanent]
  auto ({module_actions}) <module> [permanent]
  auto ({properties_actions}) ({properties}) all <args>...
  auto ({properties_actions}) ({properties}) <module> <args>...
  auto gen <text>

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

from docopt import docopt
import requests
import os
import re
import random

from json_store import JSONStore

from datetime import datetime, timedelta

class WhooshQueryModule:
    def __init__(self, name):
        self.name = name
        self.properties = JSONStore(f"{name}")
        default_dict = {
            "type": "whoosh"
            "extract": "type:subtree contains_punct:no contains_ascii:no text_len:7"
            "template": "pj on '' '{}' ''"
            "survival": 1
            "period": timedelta(hours=0.5)
        }
        for k,v in default_dict.items():
            self.properties.setdefault(k,v)


    
    def __getitem__(self, name):
        return self.properties[name]
    
    def __setitem__(self, name, value):
        self.properties[name] = value
        self.properties.sync()
    



number_pattern = re.compile("([0-9]+)(\\-([0-9]+))?(\\-([0-9]+))?")

from itertools import zip_longest
import glob
if __name__ == '__main__':
    arguments = docopt(__doc__, version='auto 0.0.1 自动命令生成', options_first=True)
    if arguments["on"]:
        with open('auto-mode.touch', "w") as f:
            pass
    elif arguments["off"]:
        os.remove('auto-mode.touch')
    elif arguments["gen"]:
        if os.path.exists('auto-mode.touch'):
            if len(arguments['<text>']) == 7:
                print(f"paiju on '' '{arguments['<text>']}' ''")
    else:
        print("未知的指令")
        exit(1)


      

