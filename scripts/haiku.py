#!/usr/local/bin/python

"""自由俳句生成器。顺序的输入关键词，等待1秒，得到俳句。
生成的俳句会保留原有关键词的顺序。
关键词不能少于三个（每句一个），而且不能多到无法顺序的组成俳句。

Usage:
  haiku on <keywords>...

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

from docopt import docopt
import requests

if __name__ == '__main__':
    arguments = docopt(__doc__, version='haiku 0.0.1', options_first=True)
    if arguments["<keywords>"]:
        print(requests.get('http://zhnlp:5000/', params={"keywords": ",".join(arguments["<keywords>"])}).text)
