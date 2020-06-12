from datetime import datetime
import numpy as np
import os

relative_path = os.path.dirname(__file__)
leap_file = 'leap-seconds.list'
date_fmt = '# %d %b %Y'
table_fmt = [('tai', 'f8'), ('leap_sec', 'f8'), ('date', datetime)]

def map_item(item):
    tai_sec, leap_sec, date = item
    return (float(tai_sec), float(leap_sec), datetime.strptime(date, date_fmt))

def leap_table():
    ''' Opens leap second list and returns a named numpy
        array of each leap second entry
    '''
    # Open leap second list and read lines
    leap_file_path = os.path.join(relative_path, leap_file)
    fd = open(leap_file_path, 'r')
    lines = fd.readlines()
    fd.close()

    # Remove comments
    items = [line.strip('\n') for line in lines if (len(line) > 0 and line[0] != '#')]

    # Split each line by tabs
    items = [item.split('\t') for item in items]

    # Map each string in line to objects and return named table
    table = list(map(map_item, items))
    table = np.array(table, dtype=table_fmt)
    return table