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

WHITELIST = {
    "ls","pwd","whoami",
    "printenv",
    "mv","cp","ln",
    "tar","unzip",
    "cat","base64",
    "grep","shuf","head","tail","cut",
}

if __name__ == '__main__':
    arguments = docopt(__doc__, version='No-bash 0.0.1', options_first=True)
    if arguments["<command>"]:
        cmd = [arguments["<command>"]] + arguments["ARGS"]
        print(f"executing {cmd}", file=sys.stderr)
        if cmd[0] in WHITELIST:
            exit(subprocess.call(cmd))
        else:
            print(f"{cmd} not in the white-list {','.join(WHITELIST)}")
            exit(1)
    elif arguments["--whitelist"]:
        print(f"You can use {','.join(WHITELIST)}")
        exit(0)
