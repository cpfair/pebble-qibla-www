from .base import Timetable
from keys import LONDON_UNIFIED_KEY
from datetime import datetime
from pytz import timezone, utc
import requests


class LondonUnified(Timetable):
    @classmethod
    def CacheKey(cls, location, date):
        return date.strftime("%Y-%m-%d")

    @classmethod
    def _mangleTime(cls, time_str, date, aft):
        time = datetime.strptime(time_str, "%H:%M").time()
        if aft:
            if time.hour < 12:
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
        return {
                "fajr":    cls._mangleTime(time_table["fajr"], date, False),
                "sunrise": cls._mangleTime(time_table["sunrise"], date, False),
                "dhuhr":   cls._mangleTime(time_table["dhuhr"], date, True),
                "asr":     cls._mangleTime(time_table["asr"], date, True),
                "maghrib": cls._mangleTime(time_table["magrib"], date, True),
                "isha":    cls._mangleTime(time_table["isha"], date, True)
        }
