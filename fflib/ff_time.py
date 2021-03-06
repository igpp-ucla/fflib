from datetime import datetime, timedelta, timezone
from dateutil import parser
import numpy as np
from bisect import bisect_left
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
    'Y1966':datetime(1966, 1, 1),
    'Y1970':datetime(1970, 1, 1),
    'Y2000':datetime(2000, 1, 1) - timedelta(seconds=ofst_delta), 
    'J2000':datetime(2000, 1, 1, 12) - timedelta(seconds=ofst_delta),
}

ff_leap_table = leap_table()

def get_leap(date):
    if ff_leap_table['date'][0] > date:
        base_leap = 0
    else:
        index = bisect_left(ff_leap_table['date'], date)
        if index >= len(ff_leap_table) or ff_leap_table['date'][index] != date:
            index = max(index - 1, 0)
        base_leap = ff_leap_table['leap_sec'][index]
    return base_leap

def date_to_tick(date, epoch, fold_mode=False):
    ''' Maps a datetime object to seconds since epoch 
    
        fold_mode specifies whether leap seconds are
        indicated by a fold=1 attribute for a datetime;
        otherwise, map to leap datetimes to
        value past leap second
    '''

    return dates_to_ticks([date], epoch, fold_mode)[0]

def dates_to_ticks(dates, epoch, fold_mode=False):
    # Check if empty
    if len(dates) == 0:
        return []

    # Check if dates have tzinfo and remove
    tzinfo = dates[0].tzinfo
    if tzinfo is not None:
        dates = [dt.replace(tzinfo=None) for dt in dates]

    # Get base leap second
    epoch_dt = epoch_to_dt[epoch]
    if epoch != 'Y1966':
        base_leap = get_leap(epoch_dt)
    else:
        base_leap = 0

    # Find leap dates between start and end dates
    start_dt = dates[0]
    end_dt = dates[-1]

    # Diff calculates total seconds between date and epoch date
    diff = lambda dt : (dt - epoch_dt).total_seconds()
    secs = np.array(list(map(diff, dates)))

    if epoch == 'Y1966':
        return secs

    # Find leap indices within dates range
    leap_dates = ff_leap_table['date']
    leap_indices = []
    leap_vals = []
    for i in range(0, len(leap_dates)):
        leap_date = leap_dates[i]
        if leap_date >= start_dt and leap_date < end_dt:
            index = bisect_left(dates, leap_date)
            if fold_mode:
                if (dates[index] == leap_date) and dates[index].fold == 1:
                    dates[index] = dates[index] + timedelta(seconds=1)
                elif (index+1) < len(dates) and (dates[index+1] == leap_date) and (dates[index+1].fold==1):
                    dates[index+1] = dates[index+1] + timedelta(seconds=1)
                    index = index + 1
            leap_indices.append(index)
            leap_vals.append(ff_leap_table['leap_sec'][i])

    # Set up base leaps
    ofsts = []
    if len(leap_indices) < 1 or leap_indices[0] != 0:
        ref_leap = get_leap(start_dt)
        ofsts = [ref_leap] + leap_vals
        indices = [0] + leap_indices + [len(dates)]
    else:
        ofsts = leap_vals
        indices = leap_indices + [len(dates)]

    # Substract offsets for each section
    for i in range(0, len(ofsts)):
        ref_leap = ofsts[i]
        start = indices[i]
        end = indices[i+1]
        secs[start:end] = secs[start:end] + (ref_leap - base_leap)

    return secs

def get_leap_info(epoch):
    ''' Returns leapseconds in datetime format, ticks since the given epoch, 
        and their respective leap offsets
    '''
    dates = ff_leap_table['date']
    seconds = [date_to_tick(date, epoch) for date in dates]
    leapvalues = ff_leap_table['leap_sec']
    return dates, seconds, leapvalues

def ticks_to_dates(ticks, epoch):
    ''' 
        Maps seconds relative to an epoch to datetime objects

        Returns a tuple -> (list of datetimes, indices of leap seconds)
    '''

    # Map epoch to a datetime
    epoch_dt = epoch_to_dt[epoch]

    # Get start/ending ticks
    if len(ticks) == 0:
        return np.array([])

    ticks = np.array(ticks, dtype='f8')
    t0, t1 = ticks[[0, -1]]

    # Get leapseconds datetimes, resp. ticks relative to epoch, and leap offsets
    dates, seconds, leapvalues = get_leap_info(epoch)
    if epoch_dt > datetime(1999, 1, 1):
        leapvalues = np.array(leapvalues) - table_delta
    
    # Find the indices where leap seconds occur (if any) and their respective offsets
    leap_offsets = []
    leap_indices = []
    base_leap_offset = 0 # Starting leap offset for time array
    true_leaps = [] # Indices where leap second timestamps occur
    for leap, leapval in zip(seconds, leapvalues):
        # If a leap second falls within range of t0 and t1
        if leap >= t0 and leap <= t1:
            index = bisect_left(ticks, leap)
            
            # If the leap second val is in the actual time array,
            # store it as a 'true_leap' to replace the timestamp for later
            if index < len(ticks) and ticks[index] == leap:
                true_leaps.append(index)
            elif index - 1 > 0 and ticks[index-1] == leap:
                true_leaps.append(index-1)

            # Find the index where this offset occurs and store it
            leap_offsets.append(leapval)
            leap_indices.append(index)

        elif leap <= t0:
            # Largest leap second <= t0 is used to set 
            # the starting offset for the array
            base_leap_offset = leapval

    # Convert time ticks to datetimes
    epoch_dt = epoch_to_dt[epoch]
    datevals = np.array([epoch_dt+timedelta(seconds=t) for t in ticks])

    # Ignore leap seconds for Y1966 epoch
    if epoch == 'Y1966':
        return datevals, []

    # Make pairs of indices to remove leap offset from
    if len(leap_indices) == 0:
        bases = [base_leap_offset]
        pairs = [0, len(ticks)]
    else:
        bases = [base_leap_offset] + leap_offsets
        pairs = [0] + leap_indices + [len(ticks)]
    
    # Adjust datetimes by leapseconds
    for z in range(0, len(bases)):
        base = bases[z]
        sI, eI = pairs[z], pairs[z+1]
        datevals[sI:eI] -= timedelta(seconds=base)

    return datevals, true_leaps

def ticks_to_iso_ts(ticks, epoch):
    ''' Converts an array of time ticks relative to the given epoch to a
        timestamp in year-month-dayThh:mm:ss.sss format
    '''
    if len(ticks) == 0:
        return np.array([])

    # Convert ticks to datetimes and get indices of leap seconds
    datevals, true_leaps = ticks_to_dates(ticks, epoch)
    
    # Convert datetimes to timestamps (%-formatting faster than strftime)
    fmt_str = '%d-%02d-%02dT%02d:%02d:%02d.%06d'
    dt_to_ts = lambda dt : (fmt_str % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond))[:-3]
    datestrs = [dt_to_ts(dt) for dt in datevals]

    # Set special timestamp for true leapseconds
    for leap_index in true_leaps:
        datestrs[leap_index] = datestrs[leap_index][:-5] + '60.000'

    return datestrs

def ticks_to_ts(ticks, epoch):
    ''' 
        Converts an array of time ticks relative to the given epoch to a
        timestamp in year month_abrv day hh:mm:ss.sss format
    '''
    if len(ticks) == 0:
        return np.array([])

    # Convert ticks to datetimes and get indices of leap seconds
    datevals, true_leaps = ticks_to_dates(ticks, epoch)
    
    # Convert datetimes to timestamps (%-formatting faster than strftime)
    dt_to_ts = lambda dt : dt.strftime(ff_fmt)
    datestrs = [dt_to_ts(dt) for dt in datevals]

    # Set special timestamp for true leapseconds
    for leap_index in true_leaps:
        datestrs[leap_index] = datestrs[leap_index][:-5] + '60.000'

    return datestrs

def tick_to_date(tick, epoch):
    ''' Converts a tick to a datetime object '''
    dates, leaps = ticks_to_dates(np.array([tick]), epoch)
    return dates[0]

def tick_to_iso_ts(tick, epoch):
    ''' Converts a tick to a timestamp in year-month-dayThh:mm:ss.sss format '''
    return ticks_to_iso_ts(np.array([tick]), epoch)[0]

def tick_to_ts(tick, epoch):
    ''' 
        Converts a tick to a timestamp in 'year month_abrv day hh:mm:ss.sss' format
    '''
    return ticks_to_ts(np.array([tick]), epoch)[0]

def utc_to_date(ts):
    fmt = '%Y %b %d %H:%M:%S.%f'
    return datetime.strptime(ts, fmt)

def iso_to_date(ts):
    date = parser.isoparse(ts)
    return date

def utc_to_iso(ts):
    ''' Maps from (year month day hh:mm:ss.sss) to year-month-dayThh:mm:ss.sss format '''
    year, mon, day, timestr = ts.split(' ')
    monstr = datetime.strptime(mon, '%b').strftime('%m')
    datestr = '-'.join([year, monstr, day])
    return f'{datestr}T{timestr}'

