#!/usr/local/bin/python

"""自由俳句生成器。顺序的输入关键词，等待1秒，得到俳句。也可以通过put和del命令编辑模板，然后使用自定义模板生成定型文，或者定制自然语言功能。
生成的俳句会保留原有关键词的顺序。
关键词不能多到无法顺序的组成俳句。
关键词中可以用问号“？”表示待定的字（由模型自行推断）。
on：体验默认俳句。
put：

Usage:
  haiku on <keywords>...
  haiku put <name> <template>
  haiku all
  haiku view <name>
  haiku del <name>
  haiku <name> <keywords>...

Options:
  -h --help     Show this screen.
  --version     Show version.
  <name>      模板名称
  <keywords>  要顺序填入模板的关键词
  <template>  模板字符串，代表了模型的目标格式文本。使用数字x表示需要x个字符；两个数字x-y表示至少填充至x个字符，但用户最多可以填入y个字符；数字x-y-z表示，至少x个字符，至多z个字符，其中用户填写最多y个字符。
"""

from docopt import docopt
import requests
import os
import re
number_pattern = re.compile("([0-9]+)(\\-([0-9]+))?(\\-([0-9]+))?")

def check_template(mode_str):
    mode_matched_indexes = [i for matched in number_pattern.finditer(mode_str) for i in matched.span()]
    mode_matched_indexes.append(0)
    mode_matched_indexes.append(len(mode_str))
    mode_matched_indexes = list(set(mode_matched_indexes))
    mode_matched_indexes.sort()
    mode = [mode_str[left:right] for left, right in zip(mode_matched_indexes[:-1], mode_matched_indexes[1:])]
    mode = [x for x in mode if x.strip()]
    mode_matched = [(i, number_pattern.match(x).groups()) for i, x in enumerate(mode) if number_pattern.match(x)]

    mode_match_index, mode_match_nums = zip(*mode_matched)
    mode_mask_min_nums = []
    mode_keyword_max_nums = []
    mode_mask_max_nums = []
    for mode_mask_min, _, mode_keyword_max, _, mode_mask_max in mode_match_nums:
        if mode_keyword_max is None:
            mode_keyword_max = mode_mask_min
        if mode_mask_max is None:
            mode_mask_max = mode_mask_min
        mode_mask_min = int(mode_mask_min)
        mode_keyword_max = int(mode_keyword_max)
        mode_mask_max = int(mode_mask_max)
        if mode_mask_max < mode_mask_min:
            mode_mask_max, mode_mask_min = mode_mask_min, mode_mask_max
        mode_mask_min_nums.append(mode_mask_min)
        mode_keyword_max_nums.append(mode_keyword_max)
        mode_mask_max_nums.append(mode_mask_max)
    assert sum(mode_mask_max_nums) <= 100, "模板要求的内容太多了。请限制在100个字符以内"

import glob
if __name__ == '__main__':
    arguments = docopt(__doc__, version='haiku 0.0.1 俳句多功能步兵车，支持定制任务', options_first=True)
    if arguments["on"]:
      print(requests.get('http://zhnlp:5000/no_self', params={"keywords": ",".join(arguments["<keywords>"])}).text)
    elif arguments["put"]:
      assert any(ch.isdigit() for ch in arguments["<template>"]), "应当至少在模板中指定一个数字来定制功能。"
      check_template(arguments["<template>"])
      with open(f"{arguments['<name>']}.txt", "w") as f:
        f.write(arguments["<template>"].strip())
    elif arguments["all"]:
      print(" ".join(x[:-4] for x in glob.glob("*.txt")))
    elif arguments["view"]:
      with open(f"{arguments['<name>']}.txt", "r") as f:
        template = f.read()
      print(template)
    elif arguments["del"]:
      os.remove(f"{arguments['<name>']}.txt")
    else: # specified <name> <keywords> to generate by templates
      with open(f"{arguments['<name>']}.txt", "r") as f:
        template = f.read()
      assert template.strip(), "模板没有内容，无法生成"
      print(requests.get('http://zhnlp:5000/no_self', params={
        "keywords": ",".join(arguments["<keywords>"]),
        "template": template.strip()
      }).text)

      

