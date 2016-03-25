class Timetable:
    @classmethod
    def CacheKey(cls, location, date):
        # Should return a cache key for Times()
        raise NotImplemented()

    @classmethod
    def Times(cls, location, date):
        # Should return a times_dict
        # Where times_dict is in the style of PrayTimes' return.
        # I.e. fractional hours since midnight for each time, in UTC.
        raise NotImplemented()
