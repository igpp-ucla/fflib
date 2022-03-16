from fflib import ff_time
from fflib.ff_time import date_to_tick, ofst_delta, tick_to_date, dates_to_ticks, ticks_to_dates
from datetime import date, datetime, timedelta

from FF_Time import FFTIME
import spiceypy as spice
import numpy as np
from fflib.leap_table import leap_table
leap_dates = leap_table()['date']
np.set_printoptions(formatter={'float':str})
spice.furnsh('latest_leapseconds.tls')

import random
random.seed(1)
epochs = ['Y1966', 'Y1970', 'Y2000', 'J2000']

def map_spice_date(d):
    ''' Maps spice string to datetime '''
    try:
        return datetime.fromisoformat(d)
    except:
        d = d.replace(':60.', ':59.')
        return datetime.fromisoformat(d)

def map_fftime_str(s):
    ''' Maps FFTIME string to datetime '''
    ff_fmt = '%Y %j %b %d %H:%M:%S.%f'
    try:
        return datetime.strptime(s, ff_fmt)
    except:
        s = s.replace(':60.', ':59.')
        return datetime.strptime(s, ff_fmt)

def ticks_to_spice_strs(ticks, epoch):
    spice_epoch = spice.et2utc(0, 'ISOC', 3)
    spice_epoch = datetime.fromisoformat(spice_epoch)
    d = date_to_tick(spice_epoch, epoch)
    spice_strs = [spice.et2utc(t-d, 'ISOC', 3) for t in ticks]
    return spice_strs

def spice_test(dates, ticks, epoch):
    spice_strs = ticks_to_spice_strs(ticks, epoch)
    spice_dates = [map_spice_date(s) for s in spice_strs]
    assert(dates == spice_dates)
    fftime_test(dates, ticks, epoch)

def fftime_test(dates, ticks, epoch):
    utc_strs = [FFTIME(t, Epoch=epoch).UTC for t in ticks]
    fftime_dates = [map_fftime_str(s) for s in utc_strs]
    if epoch in ['J2000', 'Y2000']:
        assert (dates == fftime_dates)

def string_test(ticks, epoch):
    test_iso_strs = ff_time.ticks_to_iso(ticks, epoch)
    test_isoc_strs = ff_time.ticks_to_timestamps(ticks, epoch)
    test_isoc_strs = [t[:-3] for t in test_isoc_strs]
    spice_strs = ticks_to_spice_strs(ticks, epoch)
    fftime_strs = [FFTIME(t, Epoch=epoch).UTC for t in ticks]

    assert(test_iso_strs == spice_strs)
    assert(test_isoc_strs == fftime_strs)

def comparison_tests(dates, ticks, epoch):
    spice_test(dates, ticks, epoch)
    fftime_test(dates, ticks, epoch)
    string_test(ticks, epoch)

def reversal_test(dates, epoch, ticks=None):
    if ticks is None:
        ticks = dates_to_ticks(dates, epoch)
    rev_dates = ticks_to_dates(ticks, epoch)
    assert(len(dates) == len(rev_dates))
    assert(dates == rev_dates)

def dates_tests(dates, epoch):
    ticks = dates_to_ticks(dates, epoch)
    reversal_test(dates, epoch, ticks)

max_secs = timedelta(days=30*5).total_seconds()
def get_random_dates(base, low=1, high=4):
    n = random.randint(low, high)
    dates = []
    for i in range(n):
        sec = random.randint(2, max_secs)
        di = base + timedelta(seconds=sec)
        dates.append(di)
    dates = sorted(dates)
    return dates

def leapless():
    # For every epoch
    for epoch in epochs: 
        # For every leap date choose 1-4 random dates
        # before the next leap date
        random_dates = []
        for date in leap_dates:
            dates = get_random_dates(date, 1, 4)

            # Run basic tests of dates
            dates_tests(dates, epoch)

            random_dates.extend(dates)

    # Test leapless epochs against leap dates
    leapless_epoch_tests()

def edge_leap_date_tests():
    table = leap_table()
    for epoch in ['Y2000', 'J2000']:
        epoch_dt = ff_time.epoch_to_dt[epoch]
        for tai, leap_sec, date in table[1:]:
            if date < (epoch_dt - timedelta(days=365*10)):
                continue

            if epoch_dt > datetime(1999, 1, 1):
                leap_sec -= 32

            # Single
            tick = date_to_tick(date, epoch)
            diff = (date - epoch_dt).total_seconds() + leap_sec
            assert(tick == diff)

            # Right
            prev_date = date - timedelta(seconds=1)
            ticks = dates_to_ticks([prev_date, date], epoch)
            expected_ticks = [tick-2, tick]
            assert(np.array_equal(ticks, expected_ticks))
            comparison_tests([prev_date, date], ticks, epoch)

            # Left
            next_date = date + timedelta(seconds=1)
            ticks = dates_to_ticks([date, next_date], epoch)
            expected_ticks = [tick, tick+1]
            assert(np.array_equal(ticks, expected_ticks))

            # Center
            ticks = dates_to_ticks([prev_date, date, next_date], epoch)
            expected_ticks = [tick-2, tick, tick+1]
            assert(np.array_equal(ticks, expected_ticks))

def edge_leap_tick_tests():
    table = leap_table()
    for epoch in ['Y2000', 'J2000']:
        epoch_dt = ff_time.epoch_to_dt[epoch]
        for tai, leap_sec, date in table[1:]:
            if date < (epoch_dt - timedelta(days=365*10)):
                continue

            if epoch_dt > datetime(1999, 1, 1):
                leap_sec -= 32

            # Map tick to date
            tick = date_to_tick(date, epoch)

            # Single test
            test_date = tick_to_date(tick, epoch)
            assert(date == test_date)

            # Right
            prev_tick = tick - 2
            prev_date = date - timedelta(seconds=1)
            test_ticks = [prev_tick, tick]
            test_dates = ticks_to_dates(test_ticks, epoch)
            expected_dates = [prev_date, date]

            assert(np.array_equal(test_dates, expected_dates))
            comparison_tests(test_dates, test_ticks, epoch)

            leap_tick = tick - 1
            test_ticks = [leap_tick, tick]
            test_dates = ticks_to_dates(test_ticks, epoch)
            assert(np.array_equal(test_dates, expected_dates))
            comparison_tests(test_dates, test_ticks, epoch)
            
            # Left
            next_tick = tick + 1
            next_date = date + timedelta(seconds=1)
            test_ticks = [tick, next_tick]
            test_dates = ticks_to_dates(test_ticks, epoch)
            expected_dates = [date, next_date]
            assert(np.array_equal(test_dates, expected_dates))
            comparison_tests(test_dates, test_ticks, epoch)

            # Center
            test_ticks = [prev_tick, tick, next_tick]
            test_dates = ticks_to_dates(test_ticks, epoch)
            expected_dates = [prev_date, date, next_date]
            assert(np.array_equal(test_dates, expected_dates))
            comparison_tests(test_dates, test_ticks, epoch)

            test_ticks = [prev_tick, leap_tick, tick, next_tick]
            test_dates = ticks_to_dates(test_ticks, epoch)
            expected_dates = [prev_date, prev_date, date, next_date]
            assert(np.array_equal(test_dates, expected_dates))
            comparison_tests(test_dates, test_ticks, epoch)

            # Uneven tick
            diff = 0.125
            td = timedelta(seconds=diff)
            leap_uneven_date = prev_date + td
            test_ticks = [leap_tick, leap_tick+diff, tick, next_tick]
            test_dates = ticks_to_dates(test_ticks, epoch)
            expected_dates = [prev_date, leap_uneven_date, date, next_date]
            assert(np.array_equal(test_dates, expected_dates))
            comparison_tests(test_dates, test_ticks, epoch)

            test_ticks = [leap_tick + diff]
            test_dates = ticks_to_dates(test_ticks, epoch)
            expected_dates = [leap_uneven_date]
            assert(np.array_equal(test_dates, expected_dates))
            comparison_tests(test_dates, test_ticks, epoch)

def leapless_epoch_tests():
    for epoch in ['Y1966', 'Y1970']:
        epoch_dt = ff_time.epoch_to_dt[epoch]
        for leap_date in leap_dates:
            # Leap date
            tick = date_to_tick(leap_date, epoch)
            diff = (leap_date - epoch_dt).total_seconds()
            assert(tick == diff)

            # Regular date with leap date
            other_date = leap_date - timedelta(days=1)
            other_diff = (other_date - epoch_dt).total_seconds()
            ticks = dates_to_ticks([other_date, leap_date], epoch)
            assert(np.array_equal(ticks, [other_diff, diff]))

def leap_tests():
    edge_leap_date_tests()
    edge_leap_tick_tests()

def epoch_tests():
    ''' Check that epoch date = 0 tick relative to epoch '''
    for epoch in epochs:
        date = ff_time.epoch_to_dt[epoch]
        new_date = ff_time.tick_to_date(0.0, epoch)
        assert (date == new_date)

def direct_leapless_tests():
    ''' Tests for ticks where no leap seconds need to be added '''
    dates = [datetime(year, 1, 1) for year in [1970, 1971, 2004, 2004]]
    year_seconds = timedelta(days=365).total_seconds()
    day_seconds = timedelta(days=1).total_seconds()

    # Compare 1970-1-1 relative to Y1966 epoch
    tick = ff_time.date_to_tick(dates[0], 'Y1966')
    expected_tick = year_seconds*4 + day_seconds # Add a day for leap years
    assert(tick == expected_tick)

    # Compare 1971-1-1 relative to Y1970 epoch
    tick = ff_time.date_to_tick(dates[1], 'Y1970')
    expected_tick = year_seconds
    assert(tick == expected_tick)

    # Compare 2004 relative to Y2000 epoch
    tick = ff_time.date_to_tick(dates[2], 'Y2000')
    expected_tick = year_seconds*4 + day_seconds + ofst_delta # Leap year
    assert(tick == expected_tick)

    # Compare 2004 relative to J2000 epoch
    tick = ff_time.date_to_tick(dates[3], 'J2000')
    expected_tick = expected_tick - timedelta(days=0.5).total_seconds()
    assert(tick == expected_tick)
        
def specific_tests():
    ''' Specific case tests '''
    test_date = ff_time.tick_to_date(1669835119.051, 'Y1966')
    date = datetime(2018, 11, 30, 19, 5, 19, 51000)
    assert(test_date == date)

def dates_test():
    prev = datetime(2006, 1, 1) - timedelta(seconds=1)
    leap = datetime(2005, 12, 31, 23, 59, 59, fold=1)
    post = datetime(2006, 1, 1) + timedelta(seconds=1)
    dates = [prev, leap, post]
    ticks = ff_time.dates_to_ticks(dates, 'J2000', fold_mode=True)    

def reversal_tests():
    d = datetime(2006, 1, 1)
    for epoch in ['Y1970', 'Y2000', 'J2000']:
        t = date_to_tick(d, epoch)
        rd = tick_to_date(t, epoch)
        rt = date_to_tick(rd, epoch)
        rrd = tick_to_date(rt, epoch)

        assert ((t == rt))
        assert ((d == rd))
        assert ((rd == rrd))

epoch_tests()
specific_tests()
direct_leapless_tests()
leapless()
leap_tests()
print ('All tests passed')