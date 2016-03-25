class Timetable:
    @classmethod
    def CacheKey(cls, location, date):
        # Should return a cache key for Times()
        raise NotImplemented()

    @classmethod
    def Times(cls, location, date):
        # Should return a (location_name_option, times_dict)
        # - geoname_option, if the timetable is for a fixed location.
        # - times_dict is in the style of PrayTimes' return.
        #   i.e. fractional hours since midnight for each time, in UTC.
        raise NotImplemented()
