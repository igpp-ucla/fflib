from datetime import datetime, timedelta
from dateutil import parser
import numpy as np
from bisect import bisect, bisect_left, bisect_right
from .leap_table import leap_table

# Flat file strptime/strftime format
ff_fmt = '%Y %j %b %d %H:%M:%S.%f'

# ASCII file strptime/strftime format
ts_fmt = '%Y-%m-%dT%H:%M:%S.%f'

# Seconds to offset >=Y2000 epochs by, should be 32.184 but
# this does not seem to be compatible for some reason
ofst_delta = 32
table_delta = ofst_delta # Seconds to offset leap second table vals by

# Maps epochs to datetime objects
epoch_to_dt = {
    'Y1966':datetime(1966, 1, 1), # Cline time, no leap seconds
    'Y1970':datetime(1970, 1, 1), # POSIX time
    'Y2000':datetime(2000, 1, 1) - timedelta(seconds=ofst_delta), # Ephemeris time, counts leapseconds
    'J2000':datetime(2000, 1, 1, 12) - timedelta(seconds=ofst_delta), # Julian time, counts leapseconds
}

ff_leap_table = leap_table()

def find_leaps(times, epoch, key='date', exact_leaps=False):
    ''' Searches for leap seconds to adjust for in times

        Parameters:
        -----------
        times - Seconds since epoch time or datetimes
        epoch - epoch string (needed to adjust leapseconds values)
        key - 'date' or 'leap_sec', indicates whether to search for leapseconds
            by datetime or seconds since epoch time in leap table
        exact_leaps - boolean value indicating whether to search for
            index ranges of exact leapseconds in the data if key != 'date

        Returns:
        --------
        A single list (pairs) if exact_leaps is False, otherwise a tuple
        in the form (pairs, leap_ranges) with formats as follows:
            pairs:
                A list of tuples where each tuple has the form
                    ((sI, eI), val) where sI and eI are the starting and
                    ending indices and val is the leapsecond adjustment
            leap_ranges:
                A list of tuples where each tuple has the form (sI, eI)
                indicating the starting/ending indices for true leapseconds
                in the times array
                Note: this list is empty if exact_leaps arg is False or
                    key = 'date
    '''

    # Get leap info and determine which timedelta is used
    dates, seconds, leap_vals = get_leap_info(epoch)
    date_mode = (key == 'date')
    leap_dates = dates if date_mode else seconds

    # Extract time range info
    n = len(times)
    start_time = times[0]
    stop_time = times[-1]

    # Get starting leap and index range to search for leaps
    base_leap = 0
    start = 0
    if start_time < leap_dates[0]:
        base_leap = 0
    else:
        start = bisect_left(leap_dates, start_time)
        start = max(start-1, 0)
    end = bisect_right(leap_dates, stop_time)

    # Clip leap info to current time range
    search_dates = leap_dates[start:end+1]
    search_leaps = leap_vals[start:end+1]

    if key != 'date':
        search_dates = np.array(search_dates) - 1

    # Find index each leap is at
    indices = []
    leap_ranges = []
    for date in search_dates:
        index = bisect_left(times, date)
        indices.append(index)

        # Find index where leaps end if specified
        if exact_leaps and (not date_mode):
            right_index = bisect_left(times, date+1, lo=index)
            if right_index - index > 0:
                leap_ranges.append((index, right_index))
        
    # Assemble leap info into tuples of ((sI, eI), val)
    # where (sI, eI) gives the index range and val gives the leap second
    leaps = [base_leap] + list(search_leaps)
    indices = [0] + list(indices) + [n]
    num_leaps = len(leaps)
    pairs = []
    for i in range(num_leaps):
        sI = indices[i]
        eI = indices[i+1]
        index_range = (sI, eI)
        val = leaps[i]
        if (eI - sI) > 0:
            pairs.append((index_range, val))
    
    return pairs, leap_ranges

def date_to_tick(date, epoch):
    ''' Maps a datetime object to seconds since epoch 
    '''
    return dates_to_ticks([date], epoch)[0]

def get_leap_info(epoch):
    ''' Returns leapseconds in datetime format, ticks since the given epoch, 
        and their respective leap offsets
    '''
    dates = ff_leap_table['date']
    epoch_dt = epoch_to_dt[epoch]
    diff = [(d-epoch_dt).total_seconds() for d in dates]
    leapvalues = ff_leap_table['leap_sec']
    leapvalues = [leap - table_delta for leap in leapvalues]
    seconds = [sec + leap for sec, leap in zip(diff, leapvalues)]
    return dates, seconds, leapvalues

def dates_to_ticks(dates, epoch):
    ''' Maps a list of datetime objects to seconds since epoch 

        Parameters:
        -----------
        dates: list of datetimes
        epoch: string
            string representing epoch time that ticks should be relative to

        Returns:
        --------
        ticks: array_like
            Seconds since epoch time
    '''
    # Check if empty
    if len(dates) == 0:
        return []

    # Check if dates have tzinfo and remove
    tzinfo = dates[0].tzinfo
    if tzinfo is not None:
        dates = [dt.replace(tzinfo=None) for dt in dates]

    # Calculate base difference in seconds from epoch date
    epoch_dt = epoch_to_dt[epoch]
    diff_func = lambda dt : (dt - epoch_dt).total_seconds()
    secs = np.array(list(map(diff_func, dates)))

    if epoch in ['Y1966', 'Y1970']:
        return secs

    # Get leap seconds to add
    leap_pairs, leap_ranges = find_leaps(dates, epoch, key='date')

    # Add in leap seconds to seconds
    for (sI, eI), val in leap_pairs:
        secs[sI:eI] += val

    return secs

def ticks_to_dates_helper(ticks, epoch, leap_search=True):
    '''
        Inner function used by ticks_to_dates with an additional
        leap_search argument that indicates whether to search
        for exact leap seconds values in ticks

        Left for other tools to use internally
    '''
    # Map epoch to a datetime
    epoch_dt = epoch_to_dt[epoch]
    map_func = lambda t : epoch_dt + timedelta(seconds=t)

    # Ignore leap seconds for Y1966 epoch
    if epoch in ['Y1966', 'Y1970']:
        datevals = list(map(map_func, ticks))
        return datevals, []

    # Get start/ending ticks
    if len(ticks) == 0:
        return [], []

    # Make sure ticks are a numpy array
    ticks = np.array(ticks, dtype='f8')
    n = len(ticks)

    # Get leaps to add
    pairs, leap_ranges = find_leaps(ticks, epoch, key='leap_sec', 
        exact_leaps=leap_search)

    # Add in leap seconds to seconds
    for (sI, eI), val in pairs:
        ticks[sI:eI] -= val

    # Convert time ticks to datetimes
    datevals = list(map(map_func, ticks))
    return datevals, leap_ranges

def ticks_to_dates(ticks, epoch):
    ''' 
        Maps seconds relative to an epoch to datetime objects

        Parameters:
        -----------
        ticks: array_like
            floating point values representing seconds since an epoch time
        epoch: string
            epoch that ticks should be relative to
        
        Returns:
        --------
        dates: array_like
            A list of datetimes mapped from ticks

        Note:
        -----
        ticks must be in ascending order, otherwise behavior is undefined
    '''
    dates, leaps = ticks_to_dates_helper(ticks, epoch, leap_search=False)
    return dates

def ticks_to_iso_ts(ticks, epoch):
    ''' 
        Converts an array of time ticks relative to the given epoch to a
        timestamp in year-month-dayThh:mm:ss.sss format

        Parameters:
        -----------
        ticks: array_like
            A list of seconds since epoch time in ascending order
        epoch: string
            A string representing the epoch time

        Returns:
        --------
        A list of timestamps
    '''
    if len(ticks) == 0:
        return np.array([])

    # Convert ticks to datetimes and get indices of leap seconds
    datevals, leap_ranges = ticks_to_dates_helper(ticks, epoch) 
 
    # Convert datetimes to timestamps (%-formatting faster than strftime)
    fmt_str = '%d-%02d-%02dT%02d:%02d:%02d.%06d'
    dt_to_ts = lambda dt : (fmt_str % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond))[:-3]
    datestrs = list(map(dt_to_ts, datevals))

    # Set special timestamp for true leapseconds
    replace_func = lambda s : s.replace(':59.', ':60.')
    for sI, eI in leap_ranges:
        datestrs[sI:eI] = list(map(replace_func, datestrs[sI:eI]))

    return datestrs

def ticks_to_ts(ticks, epoch):
    ''' 
        Converts an array of time ticks relative to the given epoch to a
        timestamp in "year month_abrv day hh:mm:ss.ssssss" format

        Parameters:
        -----------
        ticks: array_like
            A list of seconds since epoch time in ascending order
        epoch: string
            A string representing the epoch time

        Returns:
        --------
        A list of timestamps
    '''
    if len(ticks) == 0:
        return np.array([])

    # Convert ticks to datetimes and get indices of leap seconds
    datevals, leap_ranges = ticks_to_dates_helper(ticks, epoch)
    
    # Convert datetimes to timestamps (%-formatting faster than strftime)
    dt_to_ts = lambda dt : dt.strftime(ff_fmt)
    datestrs = [dt_to_ts(dt) for dt in datevals]

    # Set special timestamp for true leapseconds
    replace_func = lambda s : s.replace(':59.', ':60.')
    for sI, eI in leap_ranges:
        datestrs[sI:eI] = list(map(replace_func, datestrs[sI:eI]))

    return datestrs

def tick_to_date(tick, epoch):
    ''' Converts a tick to a datetime object
        See ticks_to_dates for additional info
    '''
    dates = ticks_to_dates(np.array([tick]), epoch)
    return dates[0]

def tick_to_iso_ts(tick, epoch):
    ''' Converts a tick to a timestamp in year-month-dayThh:mm:ss.sss format 
        See ticks_to_iso_ts for additional info
    '''
    return ticks_to_iso_ts(np.array([tick]), epoch)[0]

def tick_to_ts(tick, epoch):
    ''' 
        Converts a tick to a timestamp in 'year month_abrv day hh:mm:ss.sss' format
        See ticks_to_ts for additional info
    '''
    return ticks_to_ts(np.array([tick]), epoch)[0]

def utc_to_date(ts):
    ''' Converts a UTC timestamp to datetime '''
    fmt = '%Y %b %d %H:%M:%S.%f'
    return datetime.strptime(ts, fmt)

def iso_to_date(ts):
    ''' Converts ISO timestamp to datetime '''
    date = parser.isoparse(ts)
    return date

def utc_to_iso(ts):
    ''' Maps from (year month day hh:mm:ss.sss) to year-month-dayThh:mm:ss.sss format '''
    year, mon, day, timestr = ts.split(' ')
    monstr = datetime.strptime(mon, '%b').strftime('%m')
    datestr = '-'.join([year, monstr, day])
    return f'{datestr}T{timestr}'

