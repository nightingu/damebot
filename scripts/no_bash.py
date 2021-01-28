#!/usr/local/bin/python

"""It is not a bash, just a command executor. 
You can only use command in whitelist.

Usage:
  no_bash.py --whitelist
  no_bash.py <command> [ARGS...]
  no_bash.py -h | --help
  no_bash.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --whitelist   Show commands no-bash can execute.
  <command>     Command to be executed.
"""
import shlex
import sys
from docopt import docopt
import subprocess
from utils import dame

WHITELIST = [
    "ls","pwd","whoami",
    "printenv",
    "mv","cp","ln",
    "touch",
    "tar","unzip","rm",
    "cat","base64",
    "grep","shuf","head","tail","cut",
]

if __name__ == '__main__':
    arguments = docopt(__doc__, version='No-bash 0.0.1', options_first=True)
    white_list_set = set(WHITELIST)
    if arguments["<command>"]:
        cmd = [arguments["<command>"]] + arguments["ARGS"]
        if cmd[0] in white_list_set:
            print(f"executing {cmd}", file=sys.stderr)
            exit(subprocess.call(cmd))
        else:
            print(f"'{cmd[0]}' not in white-list [{' '.join(WHITELIST)}]")
            print(f"{dame(cmd)}")
            exit(1)
    elif arguments["--whitelist"]:
        print(f"You can use [{' '.join(WHITELIST)}]")
        exit(0)
