#!/usr/local/bin/python

properties = "type|extract|template|survival|period|word|cooldown"
properties_actions = "clear|set"
module_actions = "create|status|remove|on|off"

__doc__ = f"""用于控制自动回复，生成自动回复用命令，以及管理自动回复模板，自动回复条件。
你可以在其中添加支持的其他命令来使得机器人自动工作。
每个模组可以控制开关(on/off)、设置自然语言提取和命令生成模板(extract/template)以及设置触发频率(survival/period)。
开关默认会持续该模组period的时间。如果使用permanent选项则会永久开关。
调整extract命令来指定从文本中提取的内容，然后使用template来指定将要生成的命令格式。
survival控制模组的触发概率。

自然语言提取的命令格式请参考https://whoosh.readthedocs.io/en/latest/querylang.html
你可以使用auto debug <module> <text> 来调试指定模块的命令是否符合预期。auto debug <module> <text> verbose会显示更详细的信息用于调试extract命令


Usage:
  auto ({module_actions}) all [permanent]
  auto ({module_actions}) <module> [permanent]
  auto ({properties_actions}) ({properties}) all [<args>...]
  auto ({properties_actions}) ({properties}) <module> [<args>...]
  auto gen <text>
  auto debug all <text> [verbose]
  auto debug <module> <text> [verbose]


Options:
  -h --help     Show this screen.
  --version     Show version.
"""

from docopt import docopt
import requests
import os
import re
import random

import shelve

from datetime import datetime, timedelta
import pytimeparse
import urllib
import html

bool_map = {
    "1": True,
    "0": False,
    "t": True,
    "f": False,
    "y": True,
    "n": False,
    "yes": True,
    "no": False,
    "true": True,
    "False": False,
}

convert_func = dict(
    type=str,
    extract=str,
    template=str,
    survival=float,
    period=lambda s:timedelta(seconds=pytimeparse.parse(s)),
    word=lambda s:bool_map[s],
    cooldown=lambda s:timedelta(seconds=pytimeparse.parse(s)),
)

class WhooshQueryModule:
    def __init__(self, name):
        self.name = name
        self.properties = shelve.open(f"module/{name}.shelve")
        self.default_dict = {
            "type": "whoosh",
            "extract": "type:subtree contains_punct:no contains_ascii:no text_len:7",
            "word": False,
            "template": "pj on '' {} ''",
            "survival": 1,
            "period": timedelta(hours=0.5),
            "cooldown": timedelta(seconds=1),
            "on": False,
            "temporary_switch": False,
            "last_activate": datetime.now(),
        }
        for k,v in self.default_dict.items():
            self.properties.setdefault(k,v)
        self.properties.sync()

    def __str__(self):
        return f"{self.name}\n" + "\n".join(f"  {k}: {v}" for k,v in self.properties.items())

    def add(self, name, value):
        self.properties[name].append(value)
        self.properties.sync()
    
    def clear(self, name):
        self[name] = self.default_dict[name]
        self.properties.sync()

    def __getitem__(self, name):
        return self.properties[name]
    
    def switch(self, on, *, temp):
        if self["on"] != on or not temp:
            self["on"] = on
            self["temporary_switch"] = temp
        self["last_activate"] = datetime.now()
        self.properties.sync()

    def extract(self, text, text_only="no"):
        with open("test.txt", "w") as f:
            f.write(self["extract"])
        return requests.get(
            'http://spacy:5000/', data={
                "query": html.unescape(self["extract"]),
                "text_only": text_only,
                "text": html.unescape(text),
                "word_mode": "yes" if self["word"] else "no", 
                }).json()
    
    def template(self, extracted_data):
        fmt = self["template"]
        template_format_count = fmt.count('{') - fmt.count('{{') * 2
        if self["word"]:
            items = random.choice(extracted_data)
            items[template_format_count - 1] = "".join(items[template_format_count - 1:])
        else:
            items = random.sample(extracted_data, k=template_format_count)
        if not isinstance(items[0], str):
            if "text" in items[0]:
                items = [t.text for t in items]
        return fmt.format(*items)

    def gen(self, text):
        temp_expired = datetime.now() - self["last_activate"] > self["period"]
        if self["temporary_switch"] and temp_expired:
            self["on"] = not self["on"]
            self["temporary_switch"] = False
            self.properties.sync()
        if random.random() <= self["survival"] and self["on"] and datetime.now() - self["last_activate"] > self["cooldown"]:
            result = self.template(self.extract(text, text_only="yes"))
            self["last_activate"] = datetime.now()
            self.properties.sync()
            return result

    def __setitem__(self, name, value):
        self.properties[name] = value
        self.properties.sync()


number_pattern = re.compile("([0-9]+)(\\-([0-9]+))?(\\-([0-9]+))?")
from pprint import pprint

from pathlib import Path
def list_module_name():
    return [p.stem for p in Path("module").glob("*")]

def module_name(arguments, create=False):
    if arguments["all"]:
        return list_module_name()
    else:
        name = arguments["<module>"]
        if create or os.path.exists(f"module/{name}.shelve"):
            return [name]
        else:
            raise ValueError(f"不存在模组 {name}。")

from itertools import zip_longest
import glob
if __name__ == '__main__':
    arguments = docopt(__doc__, version='auto 0.0.1 自动命令生成', options_first=True)
    os.makedirs("module", exist_ok=True)
    if arguments["create"]:
        assert not arguments["all"], "你需要指定模组名来创建一个自动模组。"
        print(WhooshQueryModule(arguments["<module>"]))
    elif arguments["status"]:
        for module in module_name(arguments):
            print(WhooshQueryModule(module))
    elif arguments["remove"]:
        for module in module_name(arguments):
            os.remove(f"module/{module}.shelve")
    elif arguments["on"] or arguments["off"]:
        switch = arguments["on"]
        for module in module_name(arguments):
            WhooshQueryModule(module).switch(switch, temp=not arguments["permanent"])
    elif arguments["clear"]:
        properties_item = [name for name in properties.split("|") if arguments[name]]
        assert len(properties_item) == 1, f"你只能清除一个属性，不能{properties_item}"
        properties_item = properties_item[0]
        for module in module_name(arguments):
            WhooshQueryModule(module).clear(properties_item)
    elif arguments["set"]:
        properties_item = [name for name in properties.split("|") if arguments[name]]
        assert len(properties_item) == 1, f"你只能设置一个属性，不能{properties_item}"
        properties_item = properties_item[0]
        for module in module_name(arguments):
            WhooshQueryModule(module)[properties_item] = convert_func[properties_item](" ".join(arguments["<args>"]))
    elif arguments["gen"]:
        cmds = []
        for module in list_module_name():
            module = WhooshQueryModule(module)
            cmd = None
            try:
                cmd = module.gen(arguments["<text>"])
            except Exception:
                pass
            if cmd is not None:
                cmds.append(cmd)
        if cmds:
            print(random.choice(cmds))
    elif arguments["debug"]:
        for module in module_name(arguments):
            print(f"from {module}:")
            module = WhooshQueryModule(module)
            if arguments["verbose"]:
                result = module.extract(arguments["<text>"], text_only="no")
                if len(result) >= 1:
                    pprint(random.choice(result))
            result = module.extract(arguments["<text>"], text_only="yes")
            pprint(result)
            try:
                print(module.template(result))
            except Exception as e:
                print(e)
            

    # if arguments["on"]:
    #     with open('auto-mode.touch', "w") as f:
    #         pass
    # elif arguments["off"]:
    #     os.remove('auto-mode.touch')
    # elif arguments["gen"]:
    #     if os.path.exists('auto-mode.touch'):
    #         if len(arguments['<text>']) == 7:
    #             print(f"paiju on '' '{arguments['<text>']}' ''")
    else:
        print("未知的指令")
        exit(1)


      

