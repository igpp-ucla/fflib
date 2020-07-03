import sys
from .ff_lib import ff_reader

def fflist():
    name = sys.argv[1]
    ff = ff_reader(name)
    ff.list_header()

def ff2csv():
    name = sys.argv[1]
    ff = ff_reader(name)
    ff.to_csv()