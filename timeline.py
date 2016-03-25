from timetable import TimetableResolver
from datetime import date, time, timedelta, datetime
from collections import defaultdict
import concurrent.futures
import threading
import requests
import pytz
import json


class Timeline:
    PRAYER_NAMES =  {
        "standard": {
            "fajr": "Fajr",
            "sunrise": "Sunrise",
            "dhuhr": "Dhuhr",
            "asr": "Asr",
            "maghrib": "Maghrib",
            "isha": "Isha"
        },
        "turkish": {
            "fajr": "İmsak",
            "sunrise": "Güneş",
            "dhuhr": "Öğle",
            "asr": "İkindi",
            "maghrib": "Akşam",
            "isha": "Yatsı"
        }
    }

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
    # I'm not sure if the ThreadPoolExecutor ever shuts down threads, meaning we might need to trim this dict.
    executor_http_sessions = defaultdict(lambda: requests.Session())

    def push_pins_for_user(user, sync=False, clear=True):
        if not user.timeline_token:
            # They're not timeline-enabled
            return []
        pending_pins = []

        if clear:
            for x in range(-2, 3):
                pending_pins += Timeline._delete_pins_for_date(user, date.today() + timedelta(days=x))
        # Push pins for yesterday, today, tomorrow
        # (15s total)
        for x in range(-1, 2):
            pending_pins += Timeline._push_pins_for_date(user, date.today() + timedelta(days=x))

        if sync:
            # Wait until all our calls clear
            concurrent.futures.wait(pending_pins)
        else:
            return pending_pins

    def _push_pins_for_date(user, date):
        loc = user.location
        if hasattr(loc, "keys"):
            loc = loc['coordinates']
        loc = loc[::-1] # From the database, it's lon/lat
        geoname_option, times = TimetableResolver.Resolve(user.config["method"], user.config, loc, date)
        for key in ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]:
            yield Timeline.executor.submit(Timeline._push_time_pin, user, geoname_option, key, date, datetime.combine(date, time()).replace(tzinfo=pytz.utc) + timedelta(hours=times[key]))

    def _delete_pins_for_date(user, date):
        for key in ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]:
            yield Timeline.executor.submit(Timeline._delete_time_pin, user, key, date)

    def _delete_time_pin(user, prayer, date):
        session = Timeline.executor_http_sessions[threading.current_thread().ident]
        pin_id = "%s:%s:%s" % (user.user_token, date, prayer)
        res = session.delete("https://timeline-api.getpebble.com/v1/user/pins/%s" % pin_id,
                           headers={"X-User-Token": user.timeline_token, "Content-Type": "application/json"})
        if res.status_code == 410:
            # They've uninstalled the app
            user.timeline_token = None
            user.save()
        assert res.status_code == 200, "Pin delete failed %s %s" % (res, res.text)
        return True

    def _push_time_pin(user, geoname_option, prayer, date, timestamp):
        session = Timeline.executor_http_sessions[threading.current_thread().ident]
        pin_data = Timeline._generate_pin(user, geoname_option, prayer, date, timestamp)
        print(str(pin_data).encode("utf-8"))
        res = session.put("https://timeline-api.getpebble.com/v1/user/pins/%s" % pin_data["id"],
                           data=json.dumps(pin_data),
                           headers={"X-User-Token": user.timeline_token, "Content-Type": "application/json"})
        if res.status_code == 410:
            # They've uninstalled the app
            user.timeline_token = None
            user.save()
        assert res.status_code == 200, "Pin push failed %s %s" % (res, res.text)
        return True

    def _generate_pin(user, geoname_option, prayer, date, timestamp):
        pin_id = "%s:%s:%s" % (user.user_token, date, prayer)
        prayer_name = Timeline.PRAYER_NAMES[user.config["prayer_names"]][prayer]
        geoname = (geoname_option if geoname_option else user.location_geoname)
        return {
            "id": pin_id,
            "time": timestamp.isoformat(),
            "layout": {
                "type": "genericPin",
                "title": prayer_name,
                "subtitle": "in %s" % geoname,
                "tinyIcon": "system://images/NOTIFICATION_FLAG"
            },
            "actions": [
                {
                    "title": "Qibla Compass",
                    "type": "openWatchApp",
                    "launchCode": 20
                }
            ],
            "reminders": [
                {
                  "time": timestamp.isoformat(),
                  "layout": {
                    "type": "genericReminder",
                    "title": prayer_name,
                    "locationName": "in %s" % geoname,
                    "tinyIcon": "system://images/NOTIFICATION_FLAG"
                  }
                }
            ]
        }
