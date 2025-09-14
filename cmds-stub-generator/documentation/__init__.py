import sys

try:
    import bs4
except ModuleNotFoundError:
    import subprocess # TODO: remote, Only for dev purposes
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])

from . import index, command