from FF_Time import FFTIME
from datetime import datetime, timedelta, timezone
import numpy as np
from bisect import bisect_left
from leap_table import leap_table

# Flat file strptime/strftime format
ff_fmt = '%Y %j %b %d %H:%M:%S.%f'

# ASCII file strptime/strftime format
ts_fmt = '%Y-%m-%dT%H:%M:%S.%f'

# Maps epochs to datetime objects
epoch_to_dt = {
    'Y1966':datetime(1966, 1, 1),
    'Y1970':datetime(1970, 1, 1),
    'Y2000':datetime(2000, 1, 1), 
    'J2000':datetime(2000, 1, 1, 12),
}

ff_leap_table = leap_table()

def date_to_ff_tick(date, epoch):
    ''' Maps a datetime object to a seconds since epoch '''
    # Get initial leap seconds value from table
    epoch_dt = epoch_to_dt[epoch]
    tai_dt = datetime(1972, 1, 1)

    index = bisect_left(ff_leap_table['date'], epoch_dt)
    base_leap = ff_leap_table['leap_sec'][index]

    # Get leap seconds value of datetime passed
    index = bisect_left(ff_leap_table['date'], date)
    ref_leap = ff_leap_table['leap_sec'][index]

    diff = date - epoch_dt
    scet = diff.total_seconds() + (ref_leap - base_leap)
    return scet + 32 if epoch_dt >= epoch_to_dt['Y2000'] else scet

def get_leap_info(epoch):
    ''' Returns leapseconds in datetime format, ticks since the given epoch, 
        and their respective leap offsets
    '''
    dates = ff_leap_table['date']
    seconds = [date_to_ff_tick(date, epoch) for date in dates]
    leapvalues = ff_leap_table['leap_sec']
    return dates, seconds, leapvalues

def ff_ts_to_asc(ts):
    ''' Maps UTC timestamp from flat file to year-month-dayThh:mm:ss.sss format '''
    year, doy, mon, day, timestr = ts.split(' ')
    monstr = datetime.strptime(mon, '%b').strftime('%m')
    datestr = '-'.join([year, monstr, day])
    return f'{datestr}T{timestr}'

def ticks_to_datetimes(ticks, epoch):
    ''' 
        Maps seconds relative to an epoch to datetime objects

        Returns a tuple -> (list of datetimes, indices of leap seconds)
    '''

    # Map epoch to a datetime
    epoch_dt = epoch_to_dt[epoch]

    # Get start/ending ticks
    if len(ticks) == 0:
        return np.array([])
    if len(ticks) == 1:
        return [FFTIME(ticks[0], Epoch=epoch).UTC]

    t0, t1 = ticks[[0, -1]]

    # Get leapseconds datetimes, resp. ticks relative to epoch, and leap offsets
    dates, seconds, leapvalues = get_leap_info(epoch)

    # Find the indices where leap seconds occur (if any) and their respective offsets
    leap_offsets = []
    leap_indices = []
    base_leap_offset = 0 # Starting leap offset for time array
    true_leaps = [] # Indices where leap second timestamps occur
    for leap, leapval in zip(seconds, leapvalues):
        # If a leap second falls within range of t0 and t1
        if leap >= t0 and leap <= t1:
            # Find the index where this offset occurs and store it
            leap_offsets.append(leapval)
            index = bisect_left(ticks, leap)
            leap_indices.append(index)

            # If the leap second val is in the actual time array,
            # store it as a 'true_leap' to replace the timestamp for later
            if index < len(ticks) and ticks[index] == leap:
                true_leaps.append(index)
            elif index - 1 > 0 and ticks[index-1] == leap:
                true_leaps.append(index-1)

        elif leap < t0:
            # Largest leap second <= t0 is used to set 
            # the starting offset for the array
            base_leap_offset = leapval

    # Convert time ticks to datetimes
    epoch_dt = epoch_to_dt[epoch]
    datevals = np.array([epoch_dt+timedelta(seconds=t) for t in ticks])

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

def ticks_to_ts(ticks, epoch):
    ''' Converts an array of time ticks relative to the given epoch to a
        timestamp in year-month-dayThh:mm:ss.sss format
    '''
    if len(ticks) == 0:
        return np.array([])

    # Convert ticks to datetimes and get indices of leap seconds
    datevals, true_leaps = ticks_to_datetimes(ticks, epoch)
    
    # Convert datetimes to timestamps (%-formatting faster than strftime)
    dt_to_ts = lambda dt : ('%d-%02d-%02dT%02d:%02d:%02d.%06d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond))[:-3]
    datestrs = [dt_to_ts(dt) for dt in datevals]

    # Set special timestamp for true leapseconds
    for leap_index in true_leaps:
        # Use FFTIME to get UTC timestamp
        leap_ts = FFTIME(ticks[leap_index], Epoch=epoch).UTC

        # Map UTC timestamp to dateTtime format
        leap_ts = ff_ts_to_asc(leap_ts)

        # Replace timestamp in list
        datestrs[leap_index] = leap_ts

    return datestrs
