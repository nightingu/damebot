#!/usr/local/bin/python

"""群文件下载器，支持解包

Usage:
  download file <path>
  download package <tar_or_zip>
  download -h | --help
  download --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  <tar_or_zip>  群文件压缩包路径。支持tar.gz和7z格式。
  <path>        群文件路径
"""
import pathlib
import shlex
import sys
from docopt import docopt
import subprocess
from pathlib import Path
import os
import io
import py7zr
import tarfile


if __name__ == '__main__':
    arguments = docopt(__doc__, version='群文件下载器 0.0.2')
    if arguments["<path>"]:
      path = Path(arguments["<path>"]).resolve()
      retcode = subprocess.call(
        ["wget", "-q", "--output-document", str(path.resolve()), os.environ["BOT_DOWNLOAD_URL"]],
        stdout=subprocess.DEVNULL
      )
      print("download as ", path)
      exit(retcode)
    elif arguments["<tar_or_zip>"]:
        tar_path = Path(arguments["<tar_or_zip>"]).resolve()
        wget: subprocess.Popen = subprocess.run(
          ["wget", "-qO-", os.environ["BOT_DOWNLOAD_URL"]],
          stderr=subprocess.DEVNULL, stdout=subprocess.PIPE
        )
        retcode_tar = 1
        folder_path = tar_path.parent / tar_path.stem
        if tar_path.parts[-1].endswith(".tar.gz"):
          folder_path = folder_path.parent / folder_path.stem
          with tarfile.open(fileobj=io.BytesIO(wget.stdout), mode='r') as z:
              z.extractall(path=folder_path)
              retcode_tar = 0
        elif tar_path.parts[-1].endswith(".7z"):
          with py7zr.SevenZipFile(io.BytesIO(wget.stdout), mode='r') as z:
              z.extractall(path=folder_path)
              retcode_tar = 0
        else:
          print(f"unsupported tar {tar_path}")
        print(f"extract to {folder_path}")
        exit(retcode_tar)
    
