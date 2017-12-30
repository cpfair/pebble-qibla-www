from .base import Timetable
import datetime
from pytz import timezone, utc
import requests
import PyPDF2
import re
import io

timetable_pdfs = {
    2016: "http://www.muis.gov.sg/documents/Resource_Centre/Prayer_Timetable_2016.pdf",
    2017: "http://www.muis.gov.sg/documents/Resource_Centre/Prayer%20Timetable%202017.pdf",
    2018: "https://www.muis.gov.sg/-/media/Files/Corporate-Site/Prayer-Timetable-2018.pdf"
}

class Singapore(Timetable):
    @classmethod
    def CacheKey(cls, location, date):
        return ""

    @classmethod
    def _mangleTime(cls, time_str, date, aft):
        time = datetime.datetime.strptime(time_str.replace("\n", ""), "%H %M").time()
        if aft:
            if time.hour < 12:
                time = time.replace(hour=time.hour + 12)
        dt = timezone("Asia/Singapore").localize(datetime.datetime.combine(date, time))
        utc_dt = dt.astimezone(utc).replace(tzinfo=None)
        since_midnight = utc_dt - datetime.datetime.combine(date, datetime.datetime.min.time())
        return since_midnight.total_seconds() / 3600

    @classmethod
    def Times(cls, location, date):
        time_table_pdf_req = requests.get(timetable_pdfs[date.year])
        time_table_pdf = PyPDF2.PdfFileReader(io.BytesIO(time_table_pdf_req.content))
        results = []
        for page in time_table_pdf.pages:
            text = page.extractText()
            for time_row in re.finditer(r"(?P<date>\d+\n?/\n?\d+\n?/\n?\d{4})\s+\w+\s+(?P<fajr>\d{1,2}\s+\d\n?\d)\s+(?P<sunrise>\d{1,2}\s+\d\n?\d)\s+(?P<dhuhr>\d{1,2}\s+\d\n?\d)\s+(?P<asr>\d{1,2}\s+\d\n?\d)\s+(?P<magrib>\d{1,2}\s+\d\n?\d)\s+(?P<isha>\d{1,2}\s+\d\n?\d)", text):
                date_parts = list(int(x.strip()) for x in time_row.group("date").split("/"))
                date = datetime.date(day=date_parts[0], month=date_parts[1], year=date_parts[2])
                results.append(("Singapore", date, {
                    "fajr":    cls._mangleTime(time_row.group("fajr"), date, False),
                    "sunrise": cls._mangleTime(time_row.group("sunrise"), date, False),
                    "dhuhr":   cls._mangleTime(time_row.group("dhuhr"), date, True),
                    "asr":     cls._mangleTime(time_row.group("asr"), date, True),
                    "maghrib": cls._mangleTime(time_row.group("magrib"), date, True),
                    "isha":    cls._mangleTime(time_row.group("isha"), date, True)
                }))

        # Check nothing is missing for the year...
        missing_data = False
        last_date = None
        for result in sorted(results, key=lambda x: x[1]):
            if last_date:
                if result[1] != last_date + datetime.timedelta(days=1):
                    missing_data = True
                    print("Skip %s -> %s" % (last_date, result[1]))
            last_date = result[1]
        assert not missing_data
        assert len(results) in (365, 366)
        return results
