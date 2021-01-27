#!/usr/local/bin/python

"""It is not a bash, just a command executor.

Usage:
  no_bash.py <command> [ARGS...]
  no_bash.py -h | --help
  no_bash.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  <command>     Command to be executed.
"""
import shlex
import sys
from docopt import docopt
import subprocess

if __name__ == '__main__':
    arguments = docopt(__doc__, version='No-bash 0.0.1', options_first=True)
    if arguments["<command>"]:
        cmd = [arguments["<command>"]] + arguments["ARGS"]
        print(f"executing {cmd}", file=sys.stderr)
        exit(subprocess.call(cmd))
