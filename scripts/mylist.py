#!/usr/local/bin/python
"""自定义列表！

Usage:
  list add <list_file> <item> [before (index <item_index> | key <keyword>)]
  list batchadd <list_file> <batch_item>...
  list del <list_file> (index <item_index> | key <keyword>)
  list view <list_file> [<keyword>]
  list all [<keyword>]
  list dedup <list_file>
  list remove-list <list_file>
  list import <list_file>
  list type (normal|batch|metabatch)
  list batch <index_file> [<seperator>]
  list fullbatch <index_file> [<seperator>]
  list <list_file> 
  list -h | --help
  list --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  <list_file>   列表文件或文件夹
  <index_file>  索引文件，用来批量抽取列表
  <seperator>   批量抽取后的分隔符，默认为','。'off'视为空字符串。
  <item>        一个列表项目
  <batch_item>  一堆列表项目
  <item_index>  列表项目的索引，从1开始
  <keyword>     要搜索的关键字 
  <new_name>    列表新的名称

"""

extra = """
  list rm <list_file>
  list dedup <list_file>
  list rename <list_file> <new_name>
"""
from random import randint, choice
from typing import List
from loguru import logger
from docopt import docopt
from pathlib import Path
import os
import shutil
import ring

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

    def select_(self, index):
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

    def add_before_(self, item):
        idx = self._index
        if idx is None:
            idx = len(self.lst)
        self.lst[idx:idx] = [item]
        self._index = None
        return self

    def delete_(self):
        idx = self._index
        del self.lst[idx]
        self._index = None
        return self

    def random_(self):
        if len(self.lst) == 0:
            raise ValueError(f"{self.path} 还空空如也，无法取出一个。")
        self._index = randint(0, len(self.lst) - 1)
        return self

    def random_pick(self):
        if len(self.as_list()) == 0:
            raise ValueError(f"{self.path} 还空空如也，无法取出一个。")
        return choice(self.as_list())

    def log(self, message_func):
        print(message_func(self))
        return self

    def print(self, number=True, chain=False, number_seperator=":", item_seperator="\n"):
        # logger.debug(f"printing {self.path, self.lst, self._index ,self.index_list(), self.as_list()}")
        result = item_seperator.join(
            (f"{i+1}{number_seperator}" if number else "") + f"{x}" for i,x in enumerate(self.lst) if i in self.index_list()
        )
        if chain:
            print(result)
            return self
        else:
            return result
    
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

    def batch(self):
        return MyList(
            self.path.parent / f"{self.path.name}batch", 
            [MyList.load_file(file).random_pick() for file in self]
        )

    def __iter__(self):
        return iter(self.as_list())

    def merge_(self, other):
        self.lst.extend(other)
        return self

    def dedup_(self):
        rev_map = {k:i for i,k in reversed(list(enumerate(self)))}
        all_index = set(range(0,len(self.as_list())))
        deduped = all_index - set(rev_map.values())
        deduped = list(deduped)
        deduped.sort()
        print(f"de-duplicated '{self.path}': ")
        print(self.select_(deduped).print())
        return self.select_(all_index - set(deduped))

    @ring.lru()
    @classmethod
    def load_file(cls, file_path):
        file_path = Path(file_path)
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                return MyList(file_path, [l.strip() for l in f if l.strip() != ""])
        else:
            return MyList(file_path, [])

    @classmethod
    def load_dir_name(cls, file_path):
        file_path = Path(file_path)
        if file_path.is_dir():
            return MyList(file_path,[str(dir_file) for dir_file in file_path.iterdir() if dir_file.is_file()])
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
            for l in self:
                print(l.strip(), file=f)
    
    def remove_self(self):
        if self.path.is_file():
            print(f"remove {len(self.as_list())} items from '{self.path}'")
            os.remove(self.path)
        else:
            print(f"要移除的 '{self.path}' 不存在。")

def import_from(args):
    path = Path(args["<list_file>"]).resolve()
    if path.is_file():
        return MyList.load_file(path.parts[-1]).merge_(MyList.load_file(path)).save()
    elif path.is_dir():
        names = []
        for item in MyList.load_dir(path):
            MyList.load_file(item.path.parts[-1]).merge_(item).save()
            names.append(str(item.path.resolve()))
        return "imported:\n" + "\n".join(names)
    else:
        raise ValueError(f"未知的文件类型{path}")

all_funcs = {
    "add": lambda args: MyList.load_file(args["<list_file>"])
        .select_(index(args))
        .add_before_(args["<item>"])
        .save(),
    "del": lambda args: MyList.load_file(args["<list_file>"])
        .select_(index(args))
        .assert_one_index()
        .delete_()
        .save(),
    "": lambda args: MyList.load_file(args["<list_file>"])
        .random_()
        .as_list()[0],
    "view": lambda args: MyList.load_file(args["<list_file>"])
        .select_(index(args))
        .print(),
    "all": lambda args: MyList.load_dir_name(".")
        .select_(index(args))
        .print(number=False),
    "import": import_from,
    "batchadd": lambda args: MyList.load_file(args["<list_file>"])
        .select_(index(args))
        .merge_(args["<batch_item>"])
        .save(),
    "batch": lambda args:
        MyList.load_file(args["<index_file>"])
            .batch()
            .print(number=False, item_seperator=args["<seperator>"])
    # args["<seperator>"].join(MyList.load_file(file).random().as_list()[0]
    #     for file in MyList.load_file(args["<index_file>"]).as_list() 
    ,
    "fullbatch": lambda args: "\n".join(
        str(MyList.load_file(file).path) + args["<seperator>"] + MyList.load_file(file).random_().as_list()[0]
        for file in MyList.load_file(args["<index_file>"]).as_list() 
    ),
    "dedup": lambda args: MyList.load_file(args["<list_file>"])
        .dedup_()
        .save(),
    "remove-list": lambda args: MyList.load_file(args["<list_file>"])
        .remove_self()
    
}

def trigger(opt: str, arguments):
    result = all_funcs[opt](arguments)
    if result is not None and result.strip() != "":
        print(result, end="")
    exit(0)   

if __name__ == '__main__':
    arguments = docopt(__doc__, version='My-list自定义列表 0.1.1', options_first=True)
    if not arguments["<seperator>"]:
        arguments["<seperator>"] = ","
    if arguments["<seperator>"].strip() == "off":
        arguments["<seperator>"] = ""
    for item in all_funcs:
        if item.strip() != "" and arguments[item]:
            trigger(item, arguments)
    if all(not arguments.get(opt, False) for opt in all_funcs.keys()):
        trigger("", arguments)
    print(f"Not implemented: {arguments}")
    exit(1)
