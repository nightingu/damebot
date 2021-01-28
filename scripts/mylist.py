#!/usr/local/bin/python
"""自定义列表！

Usage:
  list add <list_file> <item> [before (index <item_index> | key <keyword>)]
  list del <list_file> (index <item_index> | key <keyword>)
  list view <list_file> [<keyword>]
  list all [<keyword>]
  list import <list_file>
  list <list_file> 
  list -h | --help
  list --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  <list_file>   列表文件
  <index_file>  索引文件，用来批量抽取列表
  <seperator>   批量抽取后的分隔符 [default: ,]
  <item>        一个列表项目
  <item_index>  列表项目的索引，从1开始
  <keyword>     要搜索的关键字 [default:  ]
  <new_name>    列表新的名称

"""

extra = """
  list rm <list_file>
  list dedup <list_file>
  list rename <list_file> <new_name>
  list batch <index_file> [<seperator>]
"""
from random import randint
from typing import List
from loguru import logger
from docopt import docopt
from pathlib import Path

import loguru

def index(args):
    """index <item_index> | word <keyword>"""
    if args["<item_index>"]:
        val:str = args["<item_index>"]
        if val.isdigit() and int(val) > 0:
            return int(val) - 1
        else:
            raise ValueError(f"{val} 需要为一个大于0的整数。")
    elif args["<keyword>"]:
        val = args["<keyword>"]
        return lambda s: val in s
    else:
        return None

class MyList:
    def __init__(self, path: Path, lst: List[str]) -> None:
        self.path = path
        self.lst = lst
        self._index = None

    def select(self, index):
        """index <item_index> | word <keyword>"""
        if callable(index):
            ids = [i for i,s in enumerate(self.lst) if index(s)]
            if len(ids) == 1:
                ids = ids[0]
            self._index = ids
        else:
            self._index = index
        return self
    
    def assert_one_index(self):
        idx = self._index
        if idx is None:
            raise ValueError("缺少 index")
        elif not isinstance(idx, int):
            raise ValueError(f"index数量太多: {idx}")    
        return self

    def add_before(self, item):
        idx = self._index
        if idx is None:
            idx = len(self.lst)
        self.lst[idx:idx] = [item]
        self._index = None
        return self

    def delete(self):
        idx = self._index
        del self.lst[idx]
        self._index = None
        return self

    def random(self):
        if len(self.lst) == 0:
            raise ValueError(f"{self.path} 还空空如也，无法取出一个。")
        self._index = randint(0, len(self.lst) - 1)
        return self

    def print(self):
        logger.debug(f"printing {self.path, self.lst, self._index ,self.index_list(), self.as_list()}")
        return "\n".join(
            f"{i+1}:{x}" for i,x in enumerate(self.lst) if i in self.index_list()
        )
    
    def index_list(self):
        idx = self._index
        idx = [idx] if isinstance(idx, int) else idx
        idx = range(0, len(self.lst)) if idx is None else idx
        return idx

    def as_list(self):
        return [x for i,x in enumerate(self.lst) if i in self.index_list()]

    def shrink(self):
        return MyList(self.path, self.as_list())

    def strip_path(self):
        self.path = Path(".") / self.path.parts[-1]
        return self

    @classmethod
    def load_file(cls, file_path):
        file_path = Path(file_path)
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                return MyList(file_path, [l.strip() for l in f if l.strip() != ""])
        else:
            return MyList(file_path, [])

    @classmethod
    def load_dir(cls, file_path):
        file_path = Path(file_path)
        if file_path.is_dir():
            return [MyList.load_file(dir_file) for dir_file in file_path.iterdir() if dir_file.is_file()]
        else:
            return []
    
    def save(self):
        # logger.debug(f"saving {self.path, self.lst, self._index ,self.index_list(), self.as_list()}")
        with open(self.path, "w", encoding="utf-8") as f:
            for l in self.as_list():
                print(l.strip(), file=f)
    

all_options = """
add
del
rm 
dedup
rename
view
all 
batch
import
""".strip().split()

def import_from(args):
    path = Path(args["<list_file>"])
    if path.is_file():
        return MyList.load_file(path).strip_path().save()
    elif path.is_dir():
        names = []
        for item in MyList.load_dir(path):
            item.strip_path().save()
            names.append(item.path)
        return "imported:" + "\n".join(names)
    else:
        raise ValueError(f"未知的文件类型{path}")

all_funcs = {
    "add": lambda args: MyList.load_file(args["<list_file>"])
        .select(index(args))
        .add_before(args["<item>"])
        .save(),
    "del": lambda args: MyList.load_file(args["<list_file>"])
        .select(index(args))
        .assert_one_index()
        .delete()
        .save(),
    "": lambda args: MyList.load_file(args["<list_file>"])
        .random()
        .as_list()[0],
    "view": lambda args: MyList.load_file(args["<list_file>"])
        .select(index(args))
        .print(),
    "all": lambda args: "\n".join(str(l.path) for l in MyList.load_dir("."))
        
}

def trigger(opt: str, arguments):
    result = all_funcs[opt](arguments)
    if result is not None and result.strip() != "":
        print(result, end="")
    exit(0)   

if __name__ == '__main__':
    arguments = docopt(__doc__, version='My-list自定义列表 0.0.1', options_first=True)
    for item in all_funcs:
        if item.strip() != "" and arguments[item]:
            trigger(item, arguments)
    if all(not arguments.get(opt, False) for opt in all_options):
        trigger("", arguments)
    print(f"Not implemented: {arguments}")
    exit(1)
