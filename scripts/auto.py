#!/usr/local/bin/python

properties = "type|extract|template|survival|period"
properties_actions = "clear|set|add"
module_actions = "create|status|remove|on|off"

f"""用于控制自动回复，生成自动回复用命令，以及管理自动回复模板，自动回复条件。
你可以在其中添加支持的其他命令来使得机器人自动工作。
每个模组可以控制开关(on/off)、设置自然语言提取和命令生成模板(extract/template)以及设置触发频率(survival/period)。
开关默认会持续该模组period的时间。如果使用permanent选项则会永久开关。

自然语言提取的命令格式请参考https://whoosh.readthedocs.io/en/latest/querylang.html
你可以使用nlp inspect <text>命令来查看支持的短语提取字段。它会默认执行type:subtree token_len:[2 TO] contains_punct:no命令来搜索两个及以上的词组成的短语（不包括标点符号）。
使用nlp test <text> <query>命令来尝试提取短语。


Usage:
  auto ({module_actions}) all [permanent]
  auto ({module_actions}) <module> [permanent]
  auto ({properties_actions}) ({properties}) all <args>...
  auto ({properties_actions}) ({properties}) <module> <args>...
  auto gen <text>
  auto nlp inspect <text>
  auto nlp test <text> <args>...

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
        self.properties = JSONStore(f"module/{name}.json")
        self.default_dict = {
            "type": "whoosh",
            "extract": "type:subtree contains_punct:no contains_ascii:no text_len:7",
            "template": "pj on '' '{}' ''",
            "survival": 1,
            "period": timedelta(hours=0.5),
        }
        for k,v in self.default_dict.items():
            self.properties.setdefault(k,v)

    def __str__(self):
        return f"{self.name}\n" + "\n".join(f"  {k}: {v}" for k,v in self.properties.items())

    def add(self, name, value):
        self.properties[name].append(value)
        self.properties.sync()
    
    def clear(self, name):
        self[name] = self.default_dict[name]

    def __getitem__(self, name):
        return self.properties[name]
    
    def extract(self, text, text_only="no"):
        return requests.get(
            'http://spacy:5000/', params={
                "query": self["extract"],
                "text_only": text_only,
                "text": text,
                }).json()
    
    def template(self, extracted_data):
        fmt = self["template"]
        template_format_count = fmt.count('{') - fmt.count('{{') * 2
        items = random.sample(extracted_data, k=template_format_count)
        if not isinstance(items[0], str):
            if "text" in items[0]:
                items = [t.text for t in items]
        return fmt.format(*items)

    def gen(self, text):
        return self.template(self.extract(text, text_only="yes"))

    def __setitem__(self, name, value):
        self.properties[name] = value
        self.properties.sync()


number_pattern = re.compile("([0-9]+)(\\-([0-9]+))?(\\-([0-9]+))?")

from itertools import zip_longest
import glob
if __name__ == '__main__':
    arguments = docopt(__doc__, version='auto 0.0.1 自动命令生成', options_first=True)
    os.makedirs("module", exist_ok=True)
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


      

