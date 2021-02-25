#!/usr/local/bin/python

"""猫猫机。

Usage:
  nyan <keywords>...

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

from docopt import docopt
from pypinyin.core import pinyin
import requests
from pypinyin import lazy_pinyin, Style
from zhon.pinyin import numbered_syllable
from random import choices
from difflib import SequenceMatcher
import re

if __name__ == '__main__':
    arguments = docopt(__doc__, version='nyan 0.0.1', options_first=True)
    if arguments["<keywords>"]:
        style = Style.TONE3
        text = " ".join(arguments["<keywords>"])
        pinyins = lazy_pinyin(text, style=style)
        miao_pinyin = lazy_pinyin('喵', style=style)[0]
        pinyin_zip = []
        text_i = 0
        for pinyin_item in pinyins:
            if re.match(numbered_syllable, pinyin_item):
                pinyin_zip.append((pinyin_item, text[text_i]))
                text_i += 1
            else:
                # default: no change
                pinyin_zip.append((pinyin_item, pinyin_item))
                text_i += len(pinyin_item)
        nyan_text_list = []
        print(pinyin_zip)
        for pinyin, item in pinyin_zip:
            if pinyin == item:
                # it is not pinyin
                nyan_text_list.append(item)
            else:
                sim = SequenceMatcher(None, pinyin, miao_pinyin).ratio()
                nyan_item = choices(['喵', item], weights=[sim, 1-sim], k=1)[0]
                nyan_text_list.append(nyan_item)
        print(nyan_text_list)
        nyan_index = len(nyan_text_list)-2 if pinyin_zip[-1][0] == pinyin_zip[-1][1] else len(nyan_text_list)-1
        if nyan_text_list[nyan_index] != '喵':
            nyan_text_list[nyan_index+1:nyan_index+1] = ['喵']

        print(''.join(nyan_text_list))

        
