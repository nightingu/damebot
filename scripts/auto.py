#!/usr/local/bin/python

"""用于控制自动回复，生成自动回复用命令，以及管理自动回复模板，自动回复条件。
你可以在其中添加支持的其他命令来使得机器人自动工作。

Usage:
  auto on
  auto off
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
number_pattern = re.compile("([0-9]+)(\\-([0-9]+))?(\\-([0-9]+))?")
# TODO: use \p instead once Python has support to this features described in Unicode Technical Standard #18
# This only matches characters in these Unicode blocks (Unicode 13.0)
# CJK Unified Ideographs: 4E00–9FFF
# CJK Unified Ideographs Extension A: 3400-4DBF
# CJK Unified Ideographs Extension B: 20000-2A6DF
# CJK Unified Ideographs Extension C: 2A700-2B73F
# CJK Unified Ideographs Extension D: 2B740-2B81F
# CJK Unified Ideographs Extension E: 2B820-2CEAF
# CJK Unified Ideographs Extension F: 2CEB0-2EBEF
# CJK Unified Ideographs Extension G: 30000-3134F
# CJK Compatibility Ideographs: F900-FAFF
# CJK Compatibility Ideographs Supplement: 2F800-2FA1F 
haiku_pattern = re.compile("^[\u4E00-\u9FFF\u3400-\u4DBF\U00020000-\U0002A6DF\U0002A700-\U0002B73F\U0002B740-\U0002B81F\U0002B820-\U0002CEAF\U0002CEB0-\U0002EBEF\U00030000-\U0003134F\uF900-\uFAFF\U0002F800-\U0002FA1F]{7}$")

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
            if haiku_pattern.fullmatch(arguments['<text>']) is not None:
                print(f"paiju on '' '{arguments['<text>']}' ''")
    else:
        print("未知的指令")
        exit(1)


      

