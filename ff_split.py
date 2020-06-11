import numpy as np
import ff_util
import sys
from datetime import datetime, timedelta
import FF_File
import bisect
from ffCreator import createFF

def split_data(times, data, ranges):
    split_times, new_data = [], []
    for a, b in ranges:
        split_times.append(times[a:b])
        new_data.append(data[a:b])
    
    return split_times, new_data

def main():
    ff = sys.argv[1]
    
    FID = FF_File.FF_ID(ff, status=FF_File.FF_STATUS.READ | FF_File.FF_STATUS.EXIST)
    FID.open()
    epoch = FID.getEpoch()
    nRows = FID.getRows()
    records = FID.DID.sliceArray(row=1, nRow=nRows)
    ffTime = records["time"]
    ffData = records["data"]

    col_info = FID.getColumnDescriptors()

    labels, units, sources = [], [], []

    for row, name, unit, source, other in col_info[2:]:
        labels.append(name)
        units.append(unit)
        sources.append(source)

    # Get datetime slices    
    start_dt = ff_util.tick_to_date(ffTime[0], epoch)
    end_dt = ff_util.tick_to_date(ffTime[-1], epoch)

    dates = []
    # start_dt = start_dt - timedelta(seconds=start_dt.second, microseconds=start_dt.microsecond)
    td = timedelta(hours=4)
    while start_dt < end_dt:
        dates.append(start_dt)
        start_dt = start_dt + td
    dates.append(end_dt)

    # Convert slices to ranges -> ticks -> indices
    ranges = []
    for i in range(0, len(dates)-1):
        # Get date pair
        dt0 = dates[i]
        dt1 = dates[i+1]

        # Convert to time ticks
        t0 = ff_util.date_to_tick(dt0, epoch)
        t1 = ff_util.date_to_tick(dt1, epoch)

        # Convert to indices in ffTime array
        sI = bisect.bisect_right(ffTime, t0)
        if sI == 1:
            sI = 0
        eI = bisect.bisect_right(ffTime, t1)
        ranges.append((sI, eI))
    
    # Remove any empty ranges
    full_ranges = []
    for a, b in ranges:
        if a != b:
            full_ranges.append((a,b))
    
    split_times, sliced_data = split_data(ffTime, ffData, full_ranges)
    for new_times, new_data in zip(split_times, sliced_data):
        start_tick, end_tick = new_times[[0, -1]]
        start_dt, end_dt = ff_util.tick_to_date(start_tick, epoch), ff_util.tick_to_date(end_tick, epoch)
        fmt = '%Y%m%d%H%M%S'
        lbl = f'ifg_{start_dt.strftime(fmt)}_{end_dt.strftime(fmt)}'
        # print (len(new_data[0]), len(units), len(labels), len(sources))
        createFF(lbl, new_times, new_data, labels, units, sources, epoch)
    
main()