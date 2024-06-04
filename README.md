# fflib
Simplified Python Flat File Library

## Examples
## Reading files
```
from fflib import ff_reader

name = 'test'
ff = ff_reader(name)

data = ff.get_data() # Data in row-major format

times = ff.get_times() # Time column in seconds since epoch time

epoch = ff.get_epoch()

cols = ff.get_labels()
```

## Writing files
```
from fflib import ff_writer
# Data to be written to file
file_name = 'test'
times = [0,1,2,3]
data = [[0,5,5],[12,251,11],[23,444,523],[434,121,123]]
columns = ['Bx', 'By', 'Bz']
epoch = 'J2000'

# Create and set information to write to a new file
ff = ff_writer(file_name)
ff.set_epoch(epoch)
ff.set_data(times, data)
ff.set_labels(columns)

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
dates, leap_indices = ff_time.ticks_to_dates(ticks, epoch)

# Convert to year-month-dayThh:mm:ss.sss format
iso_ts = ff_time.ticks_to_iso_ts(ticks, epoch)

# Convert to year month day hh:mm:ss.sss format
ts = ff_time.ticks_to_ts(ticks, epoch)
```

# API
## ff_reader
<b>check_exists(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Checks that the header and data files exist and are not empty

<b>get_abstract(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the abstract from the header file

<b>get_data(self, include_times=False)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns data as m x n array where m = # of rows, n = # of data columns;
Optional include_times flag specifies whether to include the seconds
since epoch time array as the first column

<b>get_data_table(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns data w/ time tick column as a structured
numpy array (different from a regular np.array)

<b>get_epoch(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the epoch (in string format) of the file

<b>get_error_flag(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the error flag for the data

<b>get_labels(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the label for each column

<b>get_sources(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the sources listed for each column

<b>get_time_range(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the start/end time ticks of this file

<b>get_times(self, fmt='ticks')</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the time array

<b>get_units(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the units for each column

<b>list_header(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Prints key information from the header file and column desc table

<b>shape(self)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns the number of rows and columns in the file

<b>to_csv(self, name=None, prec=7)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Writes out the flat file data to a comma-separated-value file<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Optional name argument specifies an alternate filename to
give to the .csv file<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Optional prec argument specifies the precision for the values

## ff_writer
<b>set_abstract(self, abstract)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Sets the abstract for the header file<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Input: A list of strings (one per line)

<b>set_data(self, times, data, epoch=None)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Sets the time array (in SCET) and data in record format<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Optional epoch argument is passed to set_epoch()<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Input: 
    times - array of length m, 
    data - array of shape m x n
    epoch - string

<b>set_epoch(self, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Sets the epoch (in string-format) for the file

<b>set_error_flag(self, flag)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Sets the error flag

<b>set_labels(self, names, units=None, sources=None, time_label='SCET')</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Sets the column names for non-time columns <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Input: A list of strings<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Optional col_units and col_sources arguments are passed to
set_units() and set_sources() respectively<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Optional time_label arg specifies a label for the time column

<b>set_sources(self, col_sources)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Sets data column sources

<b>set_units(self, col_units, time_units='Seconds')</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Sets the units for non-time columns <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Input: A list of strings<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Optional time_units arg specifies the units for the time column

<b>write(self, name=None)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Writes out binary data to .ffd file and ASCII header
content to .ffh file <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Optional name argument specifies a filename to write to
other than the one passed to the instance

## ff_time

Note: Arrays of ticks, timestamps, datetimes, etc. are assumed to be increasing.

<b>date_to_tick(date, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Maps a datetime object to seconds since epoch

<b>ff_ts_to_iso(ts)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Maps UTC timestamp from flat file to year-month-dayThh:mm:ss.sss format

<b>get_leap_info(epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Returns leapseconds in datetime format, ticks since the given epoch, 
and their respective leap offsets

<b>leap_table()</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Opens leap second list and returns a named numpy
array of each leap second entry

<b>tick_to_date(tick, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Converts a tick to a datetime object

<b>tick_to_iso_str(tick, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Converts a tick to a timestamp in year-month-dayThh:mm:ss.sss format

<b>tick_to_timestamp(tick, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Converts a tick to a timestamp in 'year month_abrv day hh:mm:ss.sss' format

<b>ticks_to_dates(ticks, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Maps seconds relative to an epoch to datetime objects<br>

<b>ticks_to_iso(ticks, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Converts an array of time ticks relative to the given epoch to a
timestamp in year-month-dayThh:mm:ss.sss format

<b>ticks_to_timestamps(ticks, epoch)</b></br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Converts an array of time ticks relative to the given epoch to a
timestamp in year month_abrv day hh:mm:ss.sss format

