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
  list type (normal|bach)
  list godel <list_file> [<seperator> [<template> [<max_step>]]] [debug]
  list fullgodel <list_file> [<seperator> [<template> [<beam_len> [<max_step>]]]] [debug]
  list batch <index_file> [<seperator>] [<template>]
  list fullbatch <index_file> [<seperator>] [<template>]
  list <list_file> [<template>]
  list -h | --help
  list --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  <list_file>   列表文件或文件夹
  <index_file>  索引文件，用来批量抽取列表
  <seperator>   批量抽取后的分隔符，默认为','。'off'视为空字符串。
  <max_step>    巴赫列表展开的最大步数，默认为4。
  <item>        一个列表项目
  <batch_item>  一堆列表项目
  <item_index>  列表项目的索引，从1开始
  <keyword>     要搜索的关键字 
  <new_name>    列表新的名称
  <template>    要输出的话的模板。如果没有指定$val，模板将会变成'对 <template> 测出了 $val'
  <beam_len>    采样数量。默认为3
"""

extra = """
  list rm <list_file>
  list dedup <list_file>
  list rename <list_file> <new_name>
"""
from random import randint, choice, sample
from tempfile import template
from typing import List
from loguru import logger
from docopt import docopt
from pathlib import Path
from string import Template
from pprint import pformat
import os
import shutil
import ring
import sys

def leafs(lst):
    def rec_walk(root, root_path):
        if isinstance(root, list):
            for idx, val in enumerate(root):
                yield from rec_walk(val, root_path + [idx])
        else:
            yield root_path
    yield from rec_walk(lst, [])

def get_lst(lst, path):
    current = lst
    for item in path:
        current = current[item]
    return current

def set_lst(lst, path, value):
    current = lst
    for item in path[:-1]:
        current = current[item]
    current[path[-1]] = value

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

class OneOf(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"OneOf[{','.join(str(x) for x in self)}]"
    
    def generate(self):
        v = choice(self)
        if hasattr(v, "generate"):
            v = v.generate()
        else:
            v = [v]
        return v

class All(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"All[{','.join(str(x) for x in self)}]"
    
    def generate(self):
        v_all = []
        for item in self:
            if hasattr(item, "generate"):
                item = item.generate()
            else:
                item = [item]
            v_all.extend(item)
        return v_all


class MyList:
    def __init__(self, path: Path, lst: List[str], is_batch: bool = False) -> None:
        self.path = path
        self.lst = lst
        self.is_batch = is_batch
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

    @ring.lru()
    @property
    def is_normal(self):
        return not self.is_batch

    def batch(self):
        result = []
        for file in self:
            sublist = MyList.load_file(file)
            ls = sublist.expand()
            if not ls:
                ls = [file]
            result.extend(ls)
        return MyList(
            Path(self.path.name), 
            result
        )

    # def __bool__(self):
    #     if self.lst:
    #         return True
    #     else:
    #         return False

    def expand(self):
        if self.is_batch:
            return self.as_list()
        elif len(self.lst) > 0:
            return [self.random_pick()]
        else:
            return []

    def expand_godel(self):
        if self.is_batch:
            return self.batch().as_list()
        elif len(self.lst) > 0:
            return [self.random_pick()]
        else:
            return []

    def __len__(self):
        return len(self.as_list())

    def single_tree(self, k):
        return OneOf(self) if k > len(self) else OneOf(sample(self.as_list(), k))

    def batch_tree(self, k):
        result = []
        for file in self:
            sublist = MyList.load_file(file)
            ls = All(sublist) if sublist.is_batch else sublist.single_tree(k)
            if not ls:
                ls = OneOf([file])
            result.append(ls)
        return All(result)

    def expand_godel_tree(self, k):
        if self.is_batch:
            return self.batch_tree(k)
        else:
            return self.single_tree(k)

    def __str__(self) -> str:
        return self.print()

    def godel_tree(self, remain_step, sample_num, debug):
        if remain_step > 63:
            remain_step = 63
        root_obj = self.expand_godel_tree(sample_num)
        leaf_paths = list(leafs(root_obj))
        for _ in range(remain_step-1):
            if debug:
                print(root_obj)
            extendable_paths = [path for path in leaf_paths if len(MyList.load_file(get_lst(root_obj, path)).lst) > 0]
            if debug:
                print(extendable_paths)
            if not extendable_paths:
                break
            pick_path = choice(extendable_paths)
            if debug:
                print(pick_path)
            value = MyList.load_file(get_lst(root_obj, pick_path)).expand_godel_tree(sample_num)
            set_lst(root_obj, pick_path, value)
            leaf_paths = list(leafs(root_obj))
        return root_obj


    def godel(self, remain_step, debug):
        if remain_step > 63:
            remain_step = 63
        current = self.expand_godel()
        for _ in range(remain_step-1):
            if debug:
                print(current)
            extendable_indexes = [i for i, name in enumerate(current) if len(MyList.load_file(name).lst) > 0]
            if not extendable_indexes:
                break
            pick_batch = choice(extendable_indexes)
            current[pick_batch:pick_batch+1] = MyList.load_file(current[pick_batch]).expand_godel()
        return MyList(self.path, current)

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
        if len(str(file_path).encode()) < 63 and file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                raw_list = [l.strip() for l in f if l.strip() != ""]
                is_batch = False
                if raw_list and raw_list[0] == "batch":
                    del raw_list[0]
                    is_batch = True
                return MyList(file_path, raw_list, is_batch=is_batch)
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

def type_switch(args):
    all_list = MyList.load_dir_name(".")
    if args["normal"]:
        return all_list.select_(lambda item: MyList.load_file(item).is_normal).print()
    elif args["bach"]:
        return all_list.select_(lambda item: MyList.load_file(item).is_batch).print()
    else:
        raise ValueError("不支持的type。")

def show_syntax(args):
    tree = MyList.load_file(args["<list_file>"]).godel_tree(args["<max_step>"], args["<beam_len>"], args["debug"])
    return f'{tree} => {args["<seperator>"].join(tree.generate())}'

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
        .remove_self(),
    "type": type_switch,
    "godel": lambda args: MyList.load_file(args["<list_file>"])
        .godel(args["<max_step>"], args["debug"])
        .print(number=False, item_seperator=args["<seperator>"]),
    "fullgodel": show_syntax,
}

def trigger(opt: str, arguments):
    result = all_funcs[opt](arguments)
    template = Template(arguments["<template>"])
    if result is not None and result.strip() != "":
        print(template.substitute(result, val=result), end="")
    return 0   


def main(argv):
    arguments = docopt(__doc__, argv=argv, version='My-list自定义列表 0.1.1', options_first=True)
    if not arguments["<seperator>"]:
        arguments["<seperator>"] = ","
    if not arguments["<max_step>"]:
        arguments["<max_step>"] = 4
    if not arguments["<beam_len>"]:
        arguments["<beam_len>"] = 3
    if not arguments["<template>"]:
        arguments["<template>"] = "$val"
    elif "$val" not in arguments["<template>"]:
        arguments["<template>"] = f'对 {arguments["<template>"]} 测出了 $val'
    arguments["<max_step>"] = int(arguments["<max_step>"])
    arguments["<beam_len>"] = int(arguments["<beam_len>"])   
    if arguments["<seperator>"].strip() == "off":
        arguments["<seperator>"] = ""
    for item in all_funcs:
        if item.strip() != "" and arguments[item]:
            return trigger(item, arguments)
    if all(not arguments.get(opt, False) for opt in all_funcs.keys()):
        return trigger("", arguments)
    print(f"Not implemented: {arguments}")
    return 1

if __name__ == '__main__':
    exit(main(sys.argv[1:]))
    