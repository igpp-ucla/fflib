from datetime import datetime, timedelta
from FF_Time import FFTIME

ff_ts_fmt = '%Y %j %b %d %H:%M:%S.%f'

def date_to_tick(date, epoch):
    ts = date.strftime(ff_ts_fmt)[:-3]
    tick = FFTIME(ts, Epoch=epoch)._tick
    return tick

def tick_to_date(tick, epoch):
    ts = FFTIME(tick, Epoch=epoch).UTC
    dt = datetime.strptime(ts, ff_ts_fmt)
    return dt