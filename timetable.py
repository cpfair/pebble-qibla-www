from praytimes import PrayTimes
from timetables.london_unified import LondonUnified
from timetables.malaysia import Malaysia
from models import TimetableCachedTimes

class TimetableResolver:
    _resolvers = {
        "London": LondonUnified,
        "Malaysia": Malaysia
    }

    _cache = {}

    @classmethod
    def Methods(cls):
        return list(PrayTimes.methods.keys()) + list(cls._resolvers.keys())

    @classmethod
    def Resolve(cls, method, config, location, date):
        if method in TimetableResolver._resolvers:
            # Dedicated resolver, vs. calculation.
            # We assume this lookup is costly (calling a remote API, and cache it).
            resolver = TimetableResolver._resolvers[method]
            cache_key = "%s:%s:%s" % (method, resolver.CacheKey(location, date), date.strftime("%Y-%m-%d"))
            if cache_key in TimetableResolver._cache:
                return TimetableResolver._cache[cache_key]
            try:
                cache_obj = TimetableCachedTimes.objects.get(key=cache_key)
                TimetableResolver._cache[cache_key] = cache_obj.times
                return cache_obj.times
            except TimetableCachedTimes.DoesNotExist:
                times = resolver.Times(location, date)
                TimetableResolver._cache[cache_key] = times
                TimetableCachedTimes.objects(key=cache_key).update(key=cache_key, times=times, upsert=True)
                return times
        else:
            pt = PrayTimes()
            pt.setMethod(method)
            pt.adjust({"asr": config["asr"]})
            return None, pt.getTimes(date, location, 0, format="Float")
