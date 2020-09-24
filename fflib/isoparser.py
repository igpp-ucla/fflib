from dateutil import parser
from dateutil.parser.isoparser import _takes_ascii
from datetime import datetime, timedelta, time

class ISOParser(parser.isoparser):
    ''' Subclass of dateutil's isoparser that handles
        leap seconds by mapping leap seconds to a repeated
        datetime with its fold value set to 1
    '''

    @_takes_ascii
    def isoparse(self, dt_str):
        leap = False
        components, pos = self._parse_isodate(dt_str)
        if len(dt_str) > pos:
            if self._sep is None or dt_str[pos:pos + 1] == self._sep:
                time_components = self._parse_isotime(dt_str[pos + 1:])
                if time_components[2] == 60:
                    time_components[2] = 59
                    leap = True
                components += time_components
            else:
                raise ValueError('String contains unknown ISO components')

        if len(components) > 3 and components[3] == 24:
            components[3] = 0
            res = datetime(*components, fold=int(leap)) + timedelta(days=1)

        res = datetime(*components, fold=int(leap))

        return res

    @_takes_ascii
    def parse_isotime(self, timestr):
        """
        Parse the time portion of an ISO string.
        :param timestr:
            The time portion of an ISO string, without a separator
        :return:
            Returns a :class:`datetime.time` object
        """
        components = self._parse_isotime(timestr)
        if components[0] == 24:
            components[0] = 0
        
        # Decrement by a second and set fold if leap second value
        if components[2] == 60:
            components[2] = 59
            t = time(*components, fold=1)
        else:
            t = time(*components)
        
        return t

def iso_to_date(ts):
    p = ISOParser('T')
    return p.isoparse(ts)