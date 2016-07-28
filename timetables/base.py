class Timetable:
    @classmethod
    def CacheKey(cls, location, date):
        # Should return a cache key for Times()
        raise NotImplemented()

    @classmethod
    def Times(cls, location, date):
        # Should return a list of (location_name_option, date, times_dict) tuples
        # - geoname_option, if the timetable is for a fixed location.
        # - date is a TZ-naive date
        # - times_dict is in the style of PrayTimes' return.
        #   i.e. fractional hours since midnight for each time, in UTC.
        raise NotImplemented()
