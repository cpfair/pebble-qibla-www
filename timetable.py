from praytimes import PrayTimes
from timetables.london_unified import LondonUnified
from timetables.malaysia import Malaysia
from timetables.singapore import Singapore
from models import TimetableCachedTimes

class TimetableResolver:
    _resolvers = {
        "London": LondonUnified,
        "Malaysia": Malaysia,
        "Singapore": Singapore
    }

    _cache = {}

    @classmethod
    def Methods(cls):
        return list(PrayTimes.methods.keys()) + list(cls._resolvers.keys())

    @classmethod
    def Resolve(cls, method, config, location, date):
        def buildCacheKey(loc, date):
            return "%s:%s:%s" % (method, resolver.CacheKey(loc, date), date.strftime("%Y-%m-%d"))
        if method in TimetableResolver._resolvers:
            # Dedicated resolver, vs. calculation.
            # We assume this lookup is costly (calling a remote API, and cache it).
            resolver = TimetableResolver._resolvers[method]
            query_cache_key = buildCacheKey(location, date)
            if query_cache_key in TimetableResolver._cache:
                return TimetableResolver._cache[query_cache_key]
            try:
                cache_obj = TimetableCachedTimes.objects.get(key=query_cache_key)
                TimetableResolver._cache[query_cache_key] = cache_obj.times
                return (cache_obj.location_geoname, cache_obj.times)
            except TimetableCachedTimes.DoesNotExist:
                multi_day_times = resolver.Times(location, date)
                # The resolver returns a list of (location, date, timedict) tuples.
                # Obviously the location shouldn't ever change over a range, but oh well, we're storing it discretely anyway.
                for location_geoname, date, times in multi_day_times:
                    day_cache_key = buildCacheKey(location, date)
                    TimetableResolver._cache[day_cache_key] = (location_geoname, times)
                    TimetableCachedTimes.objects(key=day_cache_key).update(key=day_cache_key, location_geoname=location_geoname, times=times, upsert=True)
                return TimetableResolver._cache[query_cache_key]
        else:
            pt = PrayTimes()
            pt.setMethod(method)
            pt.adjust({"asr": config["asr"]})
            return None, pt.getTimes(date, location, 0, format="Float")
