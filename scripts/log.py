#!/usr/local/bin/python


__doc__ = f"""用来记录消息记录。
消息将会被记录在log/<year>/<month>/<day>.jsonl中，以json形式保存所有日志。
可以对日志进行一定的搜索。

Usage:
  log data <json_text>
  log tail <number>
  log remove <year> <month> <day>



Options:
  -h --help     Show this screen.
  --version     Show version.
"""

from docopt import docopt
import json

from pprint import pprint

from pathlib import Path

from datetime import datetime

from pathlib import Path
import os
import html

def recent_events(all_list, filter=lambda x: True):
    for path in all_list:
        with path.open("r") as f:
            for item in reversed(list(f)):
                json_item = json.loads(item)
                if filter(json_item):
                    yield json_item

def pure_text(log_item):
    return "".join(t["data"]["text"] for t in log_item["message"] if "data" in t and "text" in t["data"])

def json_filter(item):
    return "message" in item and 0 < len(pure_text(item)) < 128

from datetime import datetime, tzinfo
from dateutil import tz

if __name__ == '__main__':
    arguments = docopt(__doc__, version='auto 0.0.1 自动命令生成', options_first=True)
    
    now = datetime.now()
    year, month, day = now.strftime("%Y-%m-%d").split("-")
    os.makedirs(F"log/{year}/{month}", exist_ok=True)
    if arguments["data"]:
        with open(f"log/{year}/{month}/{day}.jsonl", "a") as f:
            json_val = html.unescape(arguments["<json_text>"])
            item = json.loads(json_val)
            if item and isinstance(item, dict):
                print(json_val,file=f)
    elif arguments["tail"]:
        all_list = list(reversed(sorted(Path("log").glob("**/*.jsonl"))))
        number = int(arguments["<number>"])
        for _, log_item in zip(range(number), recent_events(all_list, filter=json_filter)):
            user = log_item["self_id"] if "api_call" in log_item else log_item["user_id"]
            time = datetime.fromtimestamp(log_item["time"])
            time = time.astimezone(tz.gettz("Asia/Shanghai"))
            time = time.strftime("%m-%d %H:%M") + " " + time.tzname()
            text = pure_text(log_item)
            print(f"{time}")
            print(f"{user}:[{text}]")
    elif arguments["remove"]:
        year, month, day = [int(arguments[x]) for x in "<year> <month> <day>".split()]
        month = "%02d" % month
        day = "%02d" % day
        year = "%04d" % year
        exit(os.remove(f"log/{year}/{month}/{day}.jsonl"))
            
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


      

