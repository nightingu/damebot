"""Usage: odd_even_example.py [-h | --help] (ODD EVEN)...

Options:
  -h, --help
"""
from docopt import docopt


if __name__ == '__main__':
    arguments = docopt(__doc__)
    print(arguments)