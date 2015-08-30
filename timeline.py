from praytimes import PrayTimes
from datetime import date, time, timedelta, datetime
import concurrent.futures
import requests
import pytz
import json


class Timeline:
    PRAYER_NAMES = {
        "fajr": "Fajr",
        "sunrise": "Sunrise",
        "dhuhr": "Dhuhr",
        "asr": "Asr",
        "maghrib": "Maghrib",
        "isha": "Isha"
    }
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
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
        pt = PrayTimes()
        pt.setMethod(user.config["method"])
        pt.adjust({"asr": user.config["asr"]})
        loc = user.location
        if hasattr(loc, "keys"):
            loc = loc['coordinates']
        loc = loc[::-1] # From the database, it's lon/lat
        times = pt.getTimes(date, loc, 0, format="Float")
        for key in ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]:
            yield Timeline.executor.submit(Timeline._push_time_pin, user, key, date, datetime.combine(date, time()).replace(tzinfo=pytz.utc) + timedelta(hours=times[key]))

    def _delete_pins_for_date(user, date):
        for key in ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]:
            yield Timeline.executor.submit(Timeline._delete_time_pin, user, key, date)

    def _delete_time_pin(user, prayer, date):
        pin_id = "%s:%s:%s" % (user.user_token, date, prayer)
        res = requests.delete("https://timeline-api.getpebble.com/v1/user/pins/%s" % pin_id,
                           headers={"X-User-Token": user.timeline_token, "Content-Type": "application/json"})
        if res.status_code == 410:
            # They've uninstalled the app
            user.timeline_token = None
            user.save()
        assert res.status_code == 200, "Pin delete failed %s %s" % (res, res.text)
        return True

    def _push_time_pin(user, prayer, date, timestamp):
        pin_data = Timeline._generate_pin(user, prayer, date, timestamp)
        print(pin_data)
        res = requests.put("https://timeline-api.getpebble.com/v1/user/pins/%s" % pin_data["id"],
                           data=json.dumps(pin_data),
                           headers={"X-User-Token": user.timeline_token, "Content-Type": "application/json"})
        if res.status_code == 410:
            # They've uninstalled the app
            user.timeline_token = None
            user.save()
        assert res.status_code == 200, "Pin push failed %s %s" % (res, res.text)
        return True

    def _generate_pin(user, prayer, date, timestamp):
        pin_id = "%s:%s:%s" % (user.user_token, date, prayer)
        return {
            "id": pin_id,
            "time": timestamp.isoformat(),
            "layout": {
                "type": "genericPin",
                "title": Timeline.PRAYER_NAMES[prayer],
                "subtitle": "in %s" % user.location_geoname,
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
                    "title": Timeline.PRAYER_NAMES[prayer],
                    "locationName": "in %s" % user.location_geoname,
                    "tinyIcon": "system://images/NOTIFICATION_FLAG"
                  }
                }
            ]
        }
