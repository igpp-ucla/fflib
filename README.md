# fflib
Simplified Python Flat File Library

# Examples
## Reading files
```
from fflib import ff_reader, ff_writer

name = 'test'
ff = ff_reader(name)

data = ff.get_data() # Data in row-major format

times = ff.get_times() # Time column in seconds since epoch time

epoch = ff.get_epoch()

cols = ff.get_column_names()
```

## Writing files
```
# Data to be written to file
file_name = 'test'
times = [0,1,2,3,4]
data = [[0,5,5],[12,251,11],[23,444,523],[434,121,123]]
columns = ['Bx', 'By', 'Bz']
epoch = 'J2000'

# Create and set information to write to a new file
ff = ff_writer(file_name)
ff.set_epoch(epoch)
ff.set_data(times, data)
ff.set_column_names(columns)

# Write to file
ff.write()
```


## Time format conversion
```
from fflib import ff_reader
from fflib import ff_time

# Read in times and epoch from a file
ff = ff_reader('test')
epoch = ff.get_epoch()
times = ff.get_times()

# Convert to datetime objects
# leap_indices contains locations of leap seconds
dates, leap_indices = ff_time.ticks_to_datetimes(ticks, epoch)

# Convert to year-month-dayThh:mm:ss.sss format
iso_ts = ff_time.ticks_to_iso_ts(ticks, epoch)

# Convert to year month day hh:mm:ss.sss format
ts = ff_time.ticks_to_ts(ticks, epoch)
```

# API
## ff_reader
<b>check_exists(self)</b></br>
Checks that the header and data files exist and are not empty

<b>get_abstract(self)</b></br>
Returns the abstract from the header file

<b>get_column_names(self)</b></br>
Returns the label for each column

<b>get_data(self, include_times=False)</b></br>
Returns data as m x n array where m = # of rows, n = # of data columns;
Optional include_times flag specifies whether to include the seconds
since epoch time array as the first column

<b>get_data_table(self)</b></br>
Returns data w/ time tick column as a structured
numpy array (different from a regular np.array)

<b>get_epoch(self)</b></br>
Returns the epoch (in string format) of the file

<b>get_error_flag(self)</b></br>
Returns the error flag for the data

<b>get_sources(self)</b></br>
Returns the sources listed for each column

<b>get_time_range(self)</b></br>
Returns the start/end time of this file

<b>get_times(self, fmt='ticks')</b></br>
Returns the time array

<b>get_units(self)</b></br>
Returns the units for each column

<b>list_header(self)</b></br>
Prints key information from the header file and column desc table

<b>shape(self)</b></br>
Returns the number of rows and columns in the file

<b>to_csv(self, name=None, prec=7, timestamps=False)</b></br>
Writes out the flat file data to a comma-separated-value file<br>Optional name argument specifies an alternate filename to
give to the .csv file; the prec argument specifies the
precision for the values
## ff_writer
<b>set_abstract(self, abstract)</b></br>
Sets the abstract for the header file<br>Input: A list of strings (one per line)

<b>set_column_names(self, col_names, col_units=None, col_sources=None)</b></br>
Sets the column names for non-time columns <br>Input: A list of strings<br>Optional col_units and col_sources arguments are passed to
set_units() and set_sources() respectively

<b>set_data(self, times, data, epoch=None)</b></br>
Sets the time array (in SCET) and data in record format<br>Optional epoch argument is passed to set_epoch()

<b>set_epoch(self, epoch)</b></br>
Sets the epoch (in string-format) for the file

<b>set_error_flag(self, flag)</b></br>
Sets the error flag

<b>set_sources(self, col_sources)</b></br>
Sets data column sources

<b>set_units(self, col_units)</b></br>
Sets the units for non-time columns <br>Input: A list of strings

<b>write(self, name=None)</b></br>
Writes out binary data to .ffd file and ASCII header
content to .ffh file <br>Optional name argument specifies a filename to write to
other than the one passed to the instance
## ff_time
<b>date_to_ff_tick(date, epoch)</b></br>
Maps a datetime object to a seconds since epoch

<b>ff_ts_to_iso(ts)</b></br>
Maps UTC timestamp from flat file to year-month-dayThh:mm:ss.sss format

<b>get_leap_info(epoch)</b></br>
Returns leapseconds in datetime format, ticks since the given epoch, 
and their respective leap offsets

<b>leap_table()</b></br>
Opens leap second list and returns a named numpy
array of each leap second entry

<b>tick_to_date(tick, epoch)</b></br>
Converts a tick to a datetime object

<b>tick_to_iso_ts(tick, epoch)</b></br>
Converts a tick to a timestamp in year-month-dayThh:mm:ss.sss format

<b>tick_to_ts(tick, epoch)</b></br>
Converts a tick to a timestamp in 'year month_abrv day hh:mm:ss.sss' format

<b>ticks_to_datetimes(ticks, epoch)</b></br>
Maps seconds relative to an epoch to datetime objects<br>Returns a tuple -> (list of datetimes, indices of leap seconds)

<b>ticks_to_iso_ts(ticks, epoch)</b></br>
Converts an array of time ticks relative to the given epoch to a
timestamp in year-month-dayThh:mm:ss.sss format

<b>ticks_to_ts(ticks, epoch)</b></br>
Converts an array of time ticks relative to the given epoch to a
timestamp in year month_abrv day hh:mm:ss.sss format
