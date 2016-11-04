from .base import Timetable
from keys import LONDON_UNIFIED_KEY
from datetime import datetime
from pytz import timezone, utc
import requests


class LondonUnified(Timetable):
    @classmethod
    def CacheKey(cls, location, date):
        return ""

    @classmethod
    def _mangleTime(cls, time_str, date, aft, maybe_morn):
        time = datetime.strptime(time_str, "%H:%M").time()
        if aft:
            # 10 allows for exceptionally early dhuhr.
            if time.hour < (10 if maybe_morn else 12):
                time = time.replace(hour=time.hour + 12)
        dt = timezone("Europe/London").localize(datetime.combine(date, time))
        utc_dt = dt.astimezone(utc).replace(tzinfo=None)
        since_midnight = utc_dt - utc_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return since_midnight.total_seconds() / 3600

    @classmethod
    def Times(cls, location, date):
        params = {
            "key": LONDON_UNIFIED_KEY,
            "format": "json",
            "date": date.strftime("%Y-%m-%d")
        }
        time_table = requests.get("http://www.londonprayertimes.com/api/times/", params=params).json()
        return (("London", date, {
                "fajr":    cls._mangleTime(time_table["fajr"], date, False, False),
                "sunrise": cls._mangleTime(time_table["sunrise"], date, False, False),
                "dhuhr":   cls._mangleTime(time_table["dhuhr"], date, True, True),
                "asr":     cls._mangleTime(time_table["asr"], date, True, False),
                "maghrib": cls._mangleTime(time_table["magrib"], date, True, False),
                "isha":    cls._mangleTime(time_table["isha"], date, True, False)
        }),)
