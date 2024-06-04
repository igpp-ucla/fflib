import re
import struct
import numpy as np
import os
from . import ff_time
from datetime import datetime
from numpy.lib import recfunctions as rfn

class ff_header():
    ''' Internal class for managing flat file header information '''
    # pre_col_keys = keys to write before the column desc table,
    # col_sections = sections in column desc table
    # col_types = numpy dtype for each column desc section
    # type_map = dict mapping col_sections to col_types
    pre_col_keys = ['DATA', 'CDATE', 'RECL', 'NCOLS', 'NROWS', 'OPSYS', 'EPOCH']
    col_sections = ['#', 'NAME', 'UNITS', 'SOURCE', 'TYPE', 'LOC']
    col_types = ['i', 'U72', 'U72', 'U72', 'U72', 'i']
    type_map = {name:dtype for name, dtype in zip(col_sections, col_types)}

    def __init__(self, ff_name, read_mode=True, copy_header=None):
        ''' Facilitates reading/writing header information for a flat file

            Requires a name to give the header file

            Optional read_mode argument specifies whether to read the
                header file initially or keep defaults
            
            Optional copy_header argument specifies another flat file to
                copy header information from
        '''
        self.name = ff_name
        self.abstract = None
        self.epoch = 'Y1966'
        self.error_flag = 1e31
        self.keyword_dict = {}
        self.col_table = None
        self._fmt_str = None

        # Read values
        if read_mode:
            self._read()
        elif copy_header is not None:
            self._read(copy_header)

        # Set initial values
        self.set_value('DATA', os.path.basename(ff_name) + '.ffd')
        self.set_value('OPSYS', 'UNKNOWN')

    def __str__(self):
        return f'Header: {self.name}'
    
    def list_info(self):
        ''' Prints key information about the header file and column desc table '''
        nrows, ncols = self.get_value('NROWS'), self.get_value('NCOLS')
        lines = [
            f'Name: {self.name}',
            f'Epoch: {self.epoch}',
            f'Flag: {self.error_flag}',
            f'Rows, Columns: {nrows}, {ncols}',
        ]

        lines += self._format_col_desc()

        print ('\n'.join(lines))
        
    def _read(self, name=None):
        ''' Reads in header .ffh file and sets internal values accordingly '''
        name = self.name if name is None else name

        # Read in characters from file
        try:
            fd = open(f'{name}.ffh', 'r')
            lines = fd.readlines()
            fd.close()
        except:
            raise Exception('Error: Could not open header file')
        
        # Split into lines w/ width = 72 characters
        lines = [lines[0][i*72:i*72+72] for i in range(0, int(len(lines[0])/72))]

        # Find the column descriptor lines
        header_start = None
        header_end = None
        index = 0
        for line in lines:
            # Split line by spaces
            items = set(line.split(' '))
            if '' in items:
                items.remove('')
            
            # Found if items split by spaces = header names
            if items == set(ff_header.col_sections):
                header_start = index
            elif line.startswith('ABSTRACT '): # Ends if abstract starts
                header_end = index
                break
            
            index += 1
        del index

        # Find end of abstract
        final_index = len(lines) 
        for i in range(header_end, len(lines)):
            # Skip everything after END line
            end_expr = '^END +$'
            if re.fullmatch(end_expr, lines[i]):
                final_index = i
                break

        if header_start is None:
            raise Exception('Error: Could not read column information')
        
        # Get all additional keyword arguments before column descriptions
        info = self._find_keywords(lines[:header_start])
        self.keyword_dict = info

        # Set error flag if given
        if 'ERROR FLAG' in info:
            self.error_flag = info['ERROR FLAG']
        else:
            info['ERROR FLAG'] = self.error_flag
        
        # Set epoch if given
        if 'EPOCH' in info:
            self.epoch = info['EPOCH']
        else:
            info['EPOCH'] = self.epoch
        
        # Get header end from key, value pairs if not found earlier
        if header_end is None:
            if 'NCOLS' in info:
                header_end = header_start + int(info['NCOLS']) + 1
            else:
                raise Exception('Error: Could not read column information')
        
        # Look for any keyword value pairs after column description
        info = self._find_keywords(lines[header_end:])
        self.keyword_dict.update(info)

        # Read in table of column info
        self.col_table = self._read_column_info(lines[header_start:header_end])

        # Save abstract
        self.abstract = lines[header_end+1:final_index]

    def _read_column_info(self, lines):
        ''' 
            Reads in column description information into a structured numpy
            array from the given set of lines
        '''
        header = lines[0]
        items = lines[1:]

        # Find the length and title of each column
        expr = '[^ ]+ *'
        headers = re.findall(expr, header)
        
        ## Add in some spaces for '#' and loc columns
        left_headers = re.findall(' +[^ ]+', header)
        headers[0] = left_headers[0]
        headers[-1] = left_headers[-1]

        char_lens = list(map(len, headers))
        header_names = [name.strip(' ') for name in headers]

        # Map lengths to character ranges for each column
        ranges = []
        a = 0
        for b in char_lens:
            ranges.append((a, a+b))
            a += b

        # Split items by columns
        split_row = lambda item : tuple([item[a:b].strip(' ') for a, b in ranges])
        rows = list(map(split_row, items))

        # Create named (and sorted) numpy table
        dtype = [(name, self.type_map[name]) for name in header_names]
        table = np.array(rows, dtype=dtype)
        table = np.sort(table, order='#')
        return table
    
    def _find_keywords(self, lines):
        ''' Find keyword value pairs in key = value format in header text 
            and returns a dictionary
        '''
        kw_expr = '[^\=]+=[^\=]+'
        info = {}
        for line in lines:
            if re.fullmatch(kw_expr, line):
                keyword, value = line.split('=')
                keyword = keyword.strip(' ')
                value = value.strip(' ')
                info[keyword] = value
        
        return info
    
    def get_desc_table(self):
        return self.col_table
    
    def get_columns(self):
        return self.col_table[self.col_sections[1]]
    
    def get_units(self):
        return self.col_table[self.col_sections[2]]
    
    def get_sources(self):
        return self.col_table[self.col_sections[3]]
    
    def get_abstract(self):
        return self.abstract
    
    def get_error_flag(self):
        return self.error_flag
    
    def get_epoch(self):
        return self.epoch
    
    def get_value(self, key):
        ''' Returns the value corresponding to some keyword in the
            header if found, otherwise returns None
        '''
        if key in self.keyword_dict:
            return self.keyword_dict[key]
        else:
            return None
    
    def set_value(self, key, value):
        ''' Updates a keyword values in header file '''
        self.keyword_dict[key] = value
    
    def format_table(table, fmt_strs):
        # Determine the length of each column
        row_lens = {}
        for key in ff_header.col_sections:
            items = table[key]
            if ff_header.type_map[key] == 'i':
                row_lens[key] = 3
            else:
                row_lens[key] = max(list(map(len, items)))
                row_lens[key] = max(row_lens[key], len(key))
        
        # Create formatting string based on column max lengths
        format_objs = [f'{{:<{row_lens[key]}}}' for key in ff_header.col_sections]
        format_objs[0] = '{:0>3}' # Zero-padded column numbers
        format_str = ' '.join(format_objs)

        if fmt_strs is not None:
            format_str = ' '.join(fmt_strs)

        # Format table entries
        lines = []
        for row in table:
            line = format_str.format(*row)
            line = '{:<72}'.format(line)
            lines.append(line)
        
        # Format header
        format_objs[0] = '{:>3}' # Adjust index padding
        format_str = ' '.join(format_objs)
        header = format_str.format(*tuple(ff_header.col_sections))
        header = '{:<72}'.format(header)

        return [header] + lines

    def _format_col_desc(self):
        ''' Formats column desc table into a list of strings
            to write to the header file
        '''
        return ff_header.format_table(self.col_table, self._fmt_str)
    
    def get_desc_string(self):
        return '\n'.join(self._format_col_desc())
    
    def set_compatible(self):
        pos = [0, 4, 14, 24, 50, 56, 60]
        lengths = np.diff(pos) - 1
        format_strs = [f'{{:<{n}}}' for n in lengths]
        format_strs[0] = '{:0>3}'
        self._fmt_str = format_strs
    
    def _format_key_val_pairs(self, keys):
        ''' Formats key-value pairs into 72-character width lines '''
        lines = []

        for key in keys:
            # Skip if not in dictionary
            if key not in self.keyword_dict:
                continue
            txt = f'{key} = {self.keyword_dict[key]}'
            line = '{:<72}'.format(txt)
            lines.append(line)
        
        return lines
    
    def write(self, name=None):
        ''' Writes header file to {name}.ffh '''
        name = self.name if name is None else name
        try:
            fd = open(f'{name}.ffh', 'w')
        except:
            raise Exception('Error: Could not open header file for writing')

        # Get initial keyword arguments lines
        lines = self._format_key_val_pairs(self.pre_col_keys)
        
        # Get column description table
        lines += self._format_col_desc()
        
        # Start abstract
        lines += ['{:<72}'.format('ABSTRACT')]

        # Write in rest of keywords after table
        keys = [key for key in self.keyword_dict if key not in self.pre_col_keys]
        lines += self._format_key_val_pairs(keys)

        # Write in abstract lines and ending line
        if self.abstract:
            lines += self.abstract
        
        lines += ['{:<72}'.format('END')]

        fd.write(''.join(lines))
        fd.close()

    def _init_table(self, ncol):
        ''' Initialize an empty column description table w/ the
            given number of entries '''
        self.col_table = np.zeros(ncol, dtype=self._table_dtype())

        # Fill column numbers
        self.col_table['#'] = np.arange(1, ncol+1)

        # Fill column types
        self.col_table['TYPE'] = 'R'
        self.col_table['TYPE'][0] = 'T'

        # Fill bit locations
        last_loc = 8 + ((ncol - 1) * 4)
        self.col_table['LOC'][0] = 0
        self.col_table['LOC'][1:] = np.arange(8, last_loc, 4)
    
    def get_recl(self):
        recl = self.get_value('RECL')
        if recl is None:
            if self.col_table is None:
                return 0
            else:
                last_loc = self.col_table['LOC'][-1]
                last_type = self.col_table['TYPE'][-1]
                last_length = self._type_to_bitlength(last_type)
                recl = last_loc + last_length
                self.set_value('RECL', recl)
                return recl
        return int(recl)

    def _table_dtype(self):
        dtype = [(name, self.type_map[name]) for name in self.col_sections]
        return dtype

    def _get_dtype(self):
        locs = self.col_table['LOC'].tolist()
        last_elem = 4 if self.col_table['TYPE'][-1] == 'R' else 8
        locs += [locs[-1] + last_elem]
        lengths = np.diff(locs)
        dtype = [f'>f{i}' for i in lengths if i > 0]
        return ','.join(dtype)
    
    def set_columns(self, names):
        ''' Sets column names '''
        if self.col_table is None:
            self._init_table(len(names))

        self.col_table[self.col_sections[1]] = names
    
    def set_locations(self, locs):
        self.col_table['LOC'] = locs
    
    def get_locations(self):
        return self.col_table['LOC']
    
    def set_types(self, types):
        self.col_table['TYPE'] = types
    
    def append_row(self, name, units='', src='', datatype='R'):
        table_dtype = self._table_dtype()
        if self.col_table is None:
            table = np.array([0, '', '', '', 0], dtype=table_dtype)
            row = 0
            recl = 0
        else:
            table = self.col_table
            row = self.col_table['#'][-1]
            recl = int(self.get_value('RECL'))

        row = row + 1
        loc = recl
        length = + self._type_to_bitlength(datatype)
        record = [(row, name, units, src, datatype, loc)]
        record = np.array(record, dtype=table_dtype)
        table = rfn.stack_arrays([table, record])
        self.col_table = table
        self.set_value('RECL', recl + length)

    def _type_to_bitlength(self, t):
        if t == 'R':
            return 4
        else:
            return 8

    def set_units(self, units):
        ''' Sets column units '''
        if self.col_table is None:
            self._init_table(len(units))
        
        self.col_table[self.col_sections[2]] = units

    def set_sources(self, sources):
        ''' Sets unit sources '''
        if self.col_table is None:
            self._init_table(len(sources))
        
        self.col_table[self.col_sections[3]] = sources
    
    def set_error_flag(self, flag):
        ''' Sets the error flag for the file '''
        self.error_flag = flag
        self.keyword_dict['ERROR FLAG'] = flag
    
    def set_epoch(self, epoch):
        ''' Sets the epoch for the file '''
        self.epoch = epoch
        self.keyword_dict['EPOCH'] = epoch
    
    def set_abstract(self, abstract):
        ''' Sets the abstract to be included in the header file
            Input: A list of strings
        '''
        self.abstract = ['{:<72}'.format(line) for line in abstract]
    
    def get_col_desc_table(self):
        ''' Returns structured numpy array representing the column
            description table
        '''
        if self.col_table is None:
            return np.array(self.col_table)
        else:
            return None
    
    def get_time_index(self):
        types = self.col_table['TYPE']
        if 'T' in types:
            return list(types).index('T')
        return 0
    
class ff_reader():
    fmts = ['index', 'tick', 'datetime', 'timestamps']
    def __init__(self, name):
        self.name = name
        self.data = None
        self.times = None

        self.header = ff_header(name, read_mode=self.check_exists())
    
    def __str__(self):
        return f'Flat File: {self.name}'

    def _filename(self):
        return f'{self.name}.ffd'

    def _record_length(self):
        return int(self.header.get_value('RECL'))

    def _read_data(self):
        ''' Reads in the data from the file and stores it at self.data '''
        try:
            fd = open(self._filename(), 'rb')
            data = fd.read()
            fd.close()
        except:
            raise Exception('Error: Could not open data file for reading')

        # Determine the shape of the file and the expected # of bytes in the data
        recl = self._record_length()
        rows = int(len(data)/recl)
        cols = int(self.header.get_value('NCOLS'))
        num_bytes = rows * recl

        # Convert binary records to data
        dtype = self.header._get_dtype()
        if num_bytes == len(data): # If no extra bytes detected
            # Read data from file w/ given dtype and convert to unstructured array
            data = np.fromfile(f'{self.name}.ffd', dtype, rows)
            data = rfn.structured_to_unstructured(data, dtype='f8')
        else:
            # If data length is off, split by recl and convert to non-binary
            records = [data[i*recl:(i+1)*recl] for i in range(0, rows)]
            data = [np.frombuffer(record, dtype=dtype) for record in records]
            data = np.array(data)
        
        self.data = data

        return data

    def shape(self):
        ''' Returns the number of rows and columns in the file '''
        rows = int(self.header.get_value('NROWS'))
        cols = int(self.header.get_value('NCOLS'))
        return (rows, cols)

    def check_exists(self):
        ''' Checks that the header and data files exist and are not empty '''
        header_file = f'{self.name}.ffh'
        data_file = self._filename()

        for file in [header_file, data_file]:
            if not os.path.exists(file):
                return False
            
            if os.path.getsize(file) <= 0:
                return False
        
        return True

    def list_header(self):
        ''' Prints key information from the header file and column desc table '''
        self.header.list_info()
        if self._is_filesize_valid():
            start, stop = self.get_time_range()
            start = start.isoformat()
            stop = stop.isoformat()
            range_dates = (start, stop)
            print (f'Date range: {range_dates}')

    def get_epoch(self):
        ''' Returns the epoch (in string format) of the file '''
        return self.header.get_epoch()
    
    def get_data(self, include_times=False):
        ''' Returns data as m x n array where m = # of rows, n = # of data columns;
            Optional include_times flag specifies whether to include the seconds
            since epoch time array as the first column
        '''
        if self.data is None:
            self._read_data()

        data = self.data
        if not include_times:
            data = data[:,1:]

        return data
    
    def get_times(self, fmt='ticks'):
        ''' Returns the time array 
        
            Parameters:
            -----------
            time_fmt: string
                Indicates whether to map data to 
                    ticks - seconds since epoch time
                    timestamps - strings in ISO format
                    datetimes - datetime objects
        '''
        if self.data is None:
            self._read_data()
        
        index = self.header.get_time_index()
        times = self.data[:,index]

        if fmt != 'ticks':
            times, dtype = self._map_times(times, fmt)

        return times
    
    def _map_times(self, times, time_fmt):
        if time_fmt == 'ticks':
            return (times, 'f8')
        elif time_fmt == 'timestamps':
            ts = ff_time.ticks_to_iso(times, self.get_epoch())
            n = len(ts[0])
            return (ts, f'U{n}')
        else:
            dates = ff_time.ticks_to_dates(times, self.get_epoch())
            return (dates, 'datetime64[s]')

    def get_data_table(self, time_fmt='ticks'):
        ''' 
            Returns data w/ time tick column as a structured
            numpy array (different from a regular np.array)

            Parameters:
            -----------
            time_fmt: string
                Indicates whether to map data to 
                    ticks - seconds since epoch time
                    timestamps - strings in ISO format
                    datetimes - datetime objects
        '''
        if self.data is None:
            self._read_data()

        # Create dtype w/ column names
        dtype = self._labeled_dtype()

        # Convert data table to records format
        table = rfn.unstructured_to_structured(self.data, dtype=np.dtype(dtype))

        if time_fmt != 'ticks':
            index = self.header.get_time_index()
            label = table.dtype.names[index]
            times = table[label]
            times, tdtype = self._map_times(times, time_fmt)
            dtype = table.dtype.descr[:]
            dtype[index] = (label, tdtype)
            table = table.astype(dtype)
            table[label] = times

        return table

    def _labeled_dtype(self):
        names = self.get_labels()
        dtype = self.header._get_dtype()
        dtype = [(name, t) for name, t in zip(names, dtype.split(','))]
        return dtype

    def get_labels(self):
        ''' Returns the label for each column '''
        return self.header.get_columns()
    
    def get_units(self):
        ''' Returns the units for each column '''
        return self.header.get_units()

    def get_abstract(self):
        ''' Returns the abstract from the header file '''
        return self.header.get_abstract()
    
    def get_sources(self):
        ''' Returns the sources listed for each column '''
        return self.header.get_sources()
    
    def get_error_flag(self):
        ''' Returns the error flag for the data '''
        return self.header.get_error_flag()
    
    def get_time_range(self):
        ''' Returns start/end times of this file in datetime formats '''
        t0, t1 = self.get_tick_range()
        return ff_time.ticks_to_dates([t0, t1], self.get_epoch())
    
    def get_tick_range(self):
        ''' Returns the start/end time ticks of this file '''
        if self._is_filesize_valid() and self.data is None:
            return self._memmap_time_range()

        # Read first/last ticks from time array if data has been loaded
        t0, t1 = self.get_times()[[0, -1]]
        return (t0, t1)

    def to_csv(self, name=None, prec=7):
        ''' Writes out the flat file data to a comma-separated-value file
            
            Optional name argument specifies an alternate filename to
            give to the .csv file
            Optional prec argument specifies the precision for the values
        '''
        # Format filename
        name = f'{self.name}.csv' if name is None else f'{name}.csv'
        
        # Get data
        data = self.get_data(include_times=True)
        ncols = len(data[0])

        # Convert first column in data to ISO timestamps
        epoch = self.get_epoch()
        timestamps = ff_time.ticks_to_iso(data[:,0], epoch)

        # Restructure data array so first column is of string type
        dtype = np.dtype('U72' + ',>f8' * (ncols - 1))
        data = rfn.unstructured_to_structured(data, dtype=dtype)
        data['f0'] = timestamps
    
        # Format header
        col_names = self.get_labels()
        time_lbl = col_names[0]
        col_names[0] = 'TIME' if 'time' not in time_lbl.lower() else time_lbl
        header = ','.join(col_names)

        # Generate formatting string
        fmt_str = ['%s'] + [f'%.{prec}f'] * (ncols - 1)

        # Save to file
        np.savetxt(name, data, delimiter=',', header=header, fmt=fmt_str, 
            comments='')

    def _memmap_data(self):
        ''' Returns a numpy memmap array-like object representing
            the data table; This may be faster when wanting to access
            only part of a large array
        '''
        # Check if filesize matches expected filesize
        filename = self._filename()

        if not self._is_filesize_valid():
            return None

        # Attempt to open file as memmap object
        try:
            dtype = self._labeled_dtype()
            table = np.memmap(filename, dtype=dtype, mode='r', shape=None)
            return table
        except:
            return None

    def get_memmap_table(self):
        return self._memmap_data()
    
    def _memmap_time_range(self):
        # Get time column index and location
        col = self.header.get_time_index()
        loc = self.header.col_table['LOC'][col]

        # Determine location of last row
        recl = self._record_length()
        rows, cols = self.shape()
        last_row_loc = max(rows-1, 0) * recl

        # Attempt to read starting & ending time ticks
        with open(self._filename(), 'rb') as fd:
            fd.seek(loc)
            start = fd.read(8)
            start = struct.unpack('>d', start)[0]
            fd.seek(last_row_loc)
            end = fd.read(8)
            end = struct.unpack('>d', end)[0]
        
        return (start, end)
        
    def _is_filesize_valid(self):
        filesize = os.path.getsize(self._filename())
        rows, cols = self.shape()
        recl = self._record_length()
        return ((rows*recl) == filesize)

    def close(self):
        self.data = None
        self.times = None

class ff_writer():
    def __init__(self, name, copy_header=None):
        ''' 
            Facilitates writing of flat files,
            
            - Requires a 'name' argument for naming the flat file
            - Optional copy_header argument specifies another flat file
              to copy relevant information from such as column descriptions
        '''
        self.name = name
        self.header = ff_header(name, read_mode=False, copy_header=copy_header)
    
    def _data_shape_checks(self, times, data):
        ''' Performs validity checks against data and times passed to set_data '''
        if len(times) != len(data):
            raise Exception('Error: Length of times != # of records in data')
        
        if len(times) == 0 or len(data) == 0:
            raise Exception('Error: Data cannot be empty!')

    def set_epoch(self, epoch):
        ''' Sets the epoch (in string-format) for the file '''
        self.header.set_epoch(epoch)

    def set_data(self, times, data, epoch=None):
        ''' 
            Sets the time array (in SCET) and data in record format
            
            Optional epoch argument is passed to set_epoch()

            Input: 
                times - array of length m, 
                data - array of shape m x n
                epoch - string
        '''
        # Make sure data is structured correctly
        self._data_shape_checks(times, data)

        # Set data array
        times = np.reshape(times, (len(times), 1))
        self.data = np.hstack([times, data])

        # Update header to reflect number of and rows
        rows, cols = self.data.shape
        self.header.set_value('NCOLS', cols)
        self.header.set_value('NROWS', rows)

        # Set epoch if given
        if epoch:
            self.set_epoch(epoch)
    
    def set_labels(self, names, units=None, sources=None,
        time_label='SCET'):
        ''' 
            Sets the column names for non-time columns 
            
            Input: A list of strings

            Optional col_units and col_sources arguments are passed to
            set_units() and set_sources() respectively

            Optional time_label arg specifies a label for the time column
        '''
        desc_table = self.header.get_desc_table()
        if desc_table is not None and desc_table.shape[0] != (len(names) + 1):
            raise Exception('List length != # of columns in description table')

        names = [time_label] + names
        self.header.set_columns(names)

        if units is not None:
            self.set_units(units)
        
        if sources is not None:
            self.set_units(sources)

    def set_units(self, col_units,
        time_units='Seconds'):
        ''' 
            Sets the units for non-time columns 

            Input: A list of strings

            Optional time_units arg specifies the units for the time column
        '''
        desc_table = self.header.get_desc_table()
        if desc_table is not None and desc_table.shape[0] != (len(col_units) + 1):
            raise Exception('List length != # of columns in description table')

        col_units = [time_units] + col_units
        self.header.set_units(col_units)
    
    def set_sources(self, col_sources):
        ''' Sets data column sources '''
        desc_table = self.header.get_desc_table()
        if desc_table is not None and desc_table.shape[0] != (len(col_sources) + 1):
            raise Exception('List length != # of columns in description table')

        sources = [''] + col_sources
        self.header.set_sources(sources)
    
    def set_abstract(self, abstract):
        ''' 
            Sets the abstract for the header file

            Input: A list of strings (one per line)
        '''
        self.header.set_abstract(abstract)

    def set_error_flag(self, flag):
        ''' Sets the error flag '''
        self.header.set_error_flag(flag)
    
    def write(self, name=None):
        ''' 
            Writes out binary data to .ffd file and ASCII header
            content to .ffh file 

            Optional name argument specifies a filename to write to
            other than the one passed to the instance
        '''
        if name is None:
            name = self.name

        # Make sure record length is set before writing
        recl = self.header.get_recl()

        # Get start/stop time to put in abstract
        times = self.data[:,0]
        epoch = self.header.get_epoch()
        t0, t1 = times[0], times[-1]
        d0 = ff_time.tick_to_date(t0, epoch)
        d1 = ff_time.tick_to_date(t1, epoch)
        fmt = '%Y %j %b %d %H:%M:%S.%f'
        self.header.set_value('FIRST TIME', d0.strftime(fmt))
        self.header.set_value('LAST TIME', d1.strftime(fmt))
        self.header.set_value('CDATE', datetime.today().strftime(fmt))

        # Write out header file
        self.header.write(name)

        # Convert data to binary format
        dtype = self.header._get_dtype()
        data = np.rec.fromarrays(self.data.T, dtype=dtype)
        data = data.tobytes()

        # Write binary data to file
        try:
            fd = open(f'{name}.ffd', 'wb')
            fd.write(data)
            fd.close()
        except:
            raise Exception('Error: Could not open data file for writing')
