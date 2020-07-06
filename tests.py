from fflib import ff_time
from fflib.ff_time import ofst_delta
from datetime import datetime, timedelta
epochs = list(ff_time.epoch_to_dt.keys())

def epoch_tests():
    ''' Check that epoch date = 0 tick relative to epoch '''
    for epoch in epochs:
        date = ff_time.epoch_to_dt[epoch]
        new_date = ff_time.tick_to_date(0.0, epoch)
        assert (date == new_date)

def leapless_tests():
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

def exact_leap_tests():
    ''' Tests time tick conversion for leap second values '''
    epoch_lst = ['Y1966', 'Y1970', 'Y2000', 'J2000']

    leap_dates = [datetime(1974, 1, 1), datetime(2006, 1, 1), datetime(2009, 1, 1)]

    # Y1966 should not treat leap seconds differently
    leap_tick = ff_time.date_to_tick(leap_dates[0], 'Y1966')
    dates, leaps = ff_time.ticks_to_dates([leap_tick], 'Y1966')
    assert(dates[0] == leap_dates[0])
    assert(len(leaps) == 0)

    # Test Y1970 epoch against exact leap seconds
    for leap_date in leap_dates:
        leap_tick = ff_time.date_to_tick(leap_date, 'Y1970')
        dates, leaps = ff_time.ticks_to_dates([leap_tick], 'Y1970')
        assert(len(leaps) == 1)
        assert(dates[0] == leap_date)

    # Test leap second values for 2000 epochs
    for epoch in ['Y2000', 'J2000']:
        for leap_date in leap_dates:
            leap_tick = ff_time.date_to_tick(leap_date, epoch)
            dates, leaps = ff_time.ticks_to_dates([leap_tick - 1, leap_tick], epoch)
            # Only one leap second found, leap date = previous second, 
            # and first date = last date (expected behavior)
            assert(len(leaps) == 1)
            assert(dates[1] == leap_date - timedelta(seconds=1))
            assert(dates[0] == dates[1])

def general_leap_tests():
    leap_dates = [datetime(1974, 1, 1), datetime(2006, 1, 1), datetime(2009, 1, 1)]

    # Test Y1970 epoch against exact leap seconds
    leap_ticks = []
    for leap_date in leap_dates:
        leap_tick = ff_time.date_to_tick(leap_date, 'Y1970')
        leap_ticks.append(leap_tick)
        leap_ticks.append(leap_tick+1)
    dates, leaps = ff_time.ticks_to_dates(leap_ticks, 'Y1970')

    assert(len(leaps) == 3)
    assert(leaps == [0, 2, 4])
    assert(dates[1] == (dates[0] + timedelta(seconds=1)))

    # Tests for >=2000 epochs
    for epoch in ['J2000', 'Y2000']:
        leap_ticks = []
        for leap_date in leap_dates:
            leap_tick = ff_time.date_to_tick(leap_date, epoch)
            leap_ticks.append(leap_tick)
            leap_ticks.append(leap_tick+1)
        dates, leaps = ff_time.ticks_to_dates(leap_ticks, epoch)

        assert(leap_ticks[0] < 0)
        assert(len(leaps) == 3)
        assert(leaps == [0, 2, 4])
        assert(dates[1] == (dates[0] + timedelta(seconds=1)))

    # Test with leapseconds but no exact values
    for epoch in ['J2000', 'Y2000']:
        middle_ticks = []
        for leap_date in leap_dates[1:]:
            leap_tick = ff_time.date_to_tick(leap_date, epoch)
            middle_ticks.append(leap_tick+2)
        correct_dates = [leap_dates[1] + timedelta(seconds=1), leap_dates[2] + timedelta(seconds=1)]
        dates, leaps = ff_time.ticks_to_dates(middle_ticks, epoch)

        for cd, td in zip(correct_dates, dates):
            assert(cd == td)

        assert(len(leaps) == 0)

epoch_tests()
leapless_tests()
specific_tests()
exact_leap_tests()
general_leap_tests()