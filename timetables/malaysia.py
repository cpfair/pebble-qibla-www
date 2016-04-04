from .base import Timetable
from datetime import datetime
from pytz import timezone, utc
from collections import namedtuple
import requests
import re

# All info from http://www.e-solat.gov.my/web/index.php
# Locations geocoded using Geonames and Google Maps.
Zone = namedtuple("Zone", "Code Name Geoname Location")
ZONES = (Zone("SWK01", "Zon 1 - Limbang, Sundar, Terusan, Lawas", "Limbang Sarawak", (4.75, 115.0)), Zone("TRG01", "Kuala Terengganu, Marang", "Kuala Terengganu, Marang", (5.3302, 103.1408)), Zone("TRG04", "Kemaman Dungun", "Dungun Terengganu", (4.775, 103.4162)), Zone("SGR04", "Putrajaya", "Masjid Putra Putrajaya", [2.9361, 101.6891]), Zone("SGR01", "Gombak,H.Selangor,Rawang, H.Langat,Sepang,Petaling,  S.Alam", "Kajang Selangor", (2.9927, 101.7909)), Zone("SGR03", "Kuala Lumpur", "Masjid Negara ", [3.142094, 101.691774]), Zone("SGR02", "Sabak Bernam, Kuala Selangor,  Klang, Kuala Langat", "Sabak Bernam", (3.58333, 101.11667)), Zone("PRK03", "Pengkalan Hulu, Grik dan Lenggong", "Pengkalan Hulu Perak", [5.70644, 100.999837]), Zone("KDH02", "Pendang, Kuala Muda, Yan", "Pendang, Kuala Muda, Yan", [5.993039, 100.477339]), Zone("KDH03", "Padang Terap, Sik", "Padang Terap, Sik", [6.256764, 100.611034]), Zone("KDH01", "Kota Setar, Kubang Pasu, Pokok Sena", "Masjid Zahir Alor Setar", [6.120343, 100.365141]), Zone("KDH06", "Langkawi", "Langkawi", (6.32973, 99.72867)), Zone("KTN01", "K.Bharu,Bachok,Pasir Puteh,Tumpat,Pasir Mas,Tnh. Merah,Machang,Kuala Krai,Mukim Chiku", "Kota Bharu Kelantan", (6.13328, 102.2386)), Zone("MLK01", "Bandar Melaka, Alor Gajah, Jasin, Masjid Tanah, Merlimau, Nyalas", "Bandar Melaka", (2.26336, 102.25155)), Zone("KTN03", "Jeli, Gua Musang (Mukim Galas, Bertam)", "Gua Musang", (4.8823, 101.9644)), Zone("WLY02", "Labuan", "Labuan", (5.33333, 115.2)), Zone("NGS01", "Jempol, Tampin", "Jempol, Tampin", (2.8026, 102.3682)), Zone("PRK01", "Tapah,Slim River dan Tanjung Malim", "Tanjung Malim", (3.681, 101.5198)), Zone("PRK02", "Ipoh, Batu Gajah, Kampar, Sg. Siput dan Kuala Kangsar", "Ipoh", (4.5841, 101.0829)), Zone("NGS02", "Port Dickson, Seremban, Kuala Pilah, Jelebu, Rembau", "Port Dickson", (2.53718, 101.80571)), Zone("PRK04", "Temengor dan Belum", "Temengor Perak", (5.32511, 101.37435)), Zone("PRK05", "Teluk Intan, Bagan Datoh, Kg.Gajah,Sri Iskandar, Beruas,Parit,Lumut,Setiawan dan Pulau Pangkor", "Teluk Intan Perak", (4.0259, 101.0213)), Zone("PRK06", "Selama, Taiping, Bagan Serai dan Parit Buntar", "Taiping", (4.85, 100.73333)), Zone("PRK07", "Bukit Larut", "Bukit Larut", (4.86247, 100.79265)), Zone("SBH04", "Zon 4 - Tawau, Balong, Merotai, Kalabakan", "Tawau Sabah", (4.24482, 117.89115)), Zone("SBH05", "Zon 5 - Kudat, Kota Marudu, Pitas, Pulau Banggi", "Kudat Sabah", (6.5, 116.66667)), Zone("SBH06", "Zon 6 - Gunung Kinabalu", "Gunung Kinabalu Sabah", (6.07458, 116.5582)), Zone("SBH07", "Zon 7 - Papar, Ranau, Kota Belud, Tuaran, Penampang, Kota Kinabalu", "Kota Belud Sabah", (6.351, 116.4305)), Zone("SWK08", "Zon 8 - Kuching, Bau, Lundu,Sematan", "Kuching Sarawak", (1.55, 110.33333)), Zone("SBH01", "Zon 1 - Sandakan, Bdr. Bkt. Garam, Semawang, Temanggong, Tambisan", "Sandakan Sabah", (5.8402, 118.1179)), Zone("SBH02", "Zon 2 - Pinangah, Terusan, Beluran, Kuamut, Telupit", "Beluran Sabah", (5.8956, 117.5557)), Zone("SBH03", "Zon 3 - Lahad Datu, Kunak, Silabukan, Tungku, Sahabat, Semporna", "Lahad Datu Sabah", (5.0268, 118.327)), Zone("SWK04", "Zon 4 - Igan, Kanowit, Sibu, Dalat, Oya", "Sibu Sarawak", (2.3, 111.81667)), Zone("SWK05", "Zon 5 - Belawai, Matu, Daro, Sarikei, Julau, Bitangor, Rajang", "Sarikei Sarawak", (2.11667, 111.51667)), Zone("SWK06", "Zon 6 - Kabong, Lingga, Sri Aman, Engkelili, Betong, Spaoh, Pusa, Saratok, Roban, Debak", "Sri Aman Sarawak", (1.5, 111.5)), Zone("SWK07", "Zon 7 - Samarahan, Simunjan, Serian, Sebuyau, Meludam", "Samarahan Sarawak", (1.25, 110.75)), Zone("SBH08", "Zon 8 - Pensiangan, Keningau, Tambunan, Nabawan", "Keningau Sabah", (5.3378, 116.1602)), Zone("SBH09", "Zon 9 - Sipitang, Membakut, Beaufort, Kuala Penyu, Weston, Tenom, Long Pa Sia", "Beaufort Sabah", (5.3473, 115.7455)), Zone("SWK02", "Zon 2 - Niah, Belaga, Sibuti, Miri, Bekenu, Marudi", "Miri Sarawak", (4.4148, 114.0089)), Zone("SWK03", "Zon 3 - Song, Belingan, Sebauh, Bintulu, Tatau, Kapit", "Bintulu Sarawak", (3.16667, 113.03333)), Zone("JHR04", "Batu Pahat, Muar, Segamat, Gemas", "Muar", (2.0442, 102.5689)), Zone("TRG02", "Besut, Setiu", "Besut, Setiu", (5.82901, 102.55238)), Zone("TRG03", "Hulu Terengganu", "Hulu Terengganu", (5.08333, 102.8)), Zone("JHR01", "Pulau Aur dan Pemanggil ", "Pulau Aur Johor", (2.45, 104.51667)), Zone("JHR03", "Kluang dan Pontian", "Pontian", (1.4866, 103.3896)), Zone("JHR02", "Kota Tinggi, Mersing, Johor Bahru", "Kota Tinggi", (1.7381, 103.8999)), Zone("PLS01", "Kangar, Padang Besar, Arau", "Kangar, Padang Besar, Arau", (6.4414, 100.19862)), Zone("PHG02", "Kuantan, Pekan, Rompin, Muadzam Shah", "Kuantan Pahang", (3.8077, 103.326)), Zone("PHG03", "Maran, Chenor, Temerloh, Bera, Jerantut", "Temerloh Pahang", (3.4506, 102.4176)), Zone("PHG01", "Pulau Tioman", "Pulau Tioman", (2.7972, 104.166)), Zone("PHG06", "Bukit Fraser, Genting Higlands, Cameron Higlands", "Genting Higlands", [3.423978, 101.793201]), Zone("PHG04", "Bentong, Raub, Kuala Lipis", "Bentong Pahang", (3.52229, 101.90866)), Zone("PHG05", "Genting Sempah, Janda Baik, Bukit Tinggi", "Janda Baik Pahang", (3.31667, 101.86667)), Zone("SWK09", "Zon 9 - Zon Khas", "Kuching Sarawak", (1.55, 110.33333)), Zone("PNG01", "Seluruh Negeri Pulau Pinang", "Seluruh Negeri Pulau Pinang", [5.414168, 100.328759]), Zone("KDH07", "Gunung Jerai", "Gunung Jerai", (5.78756, 100.43394)), Zone("KDH04", "Baling", "Baling", (5.56578, 100.72918)), Zone("KDH05", "Kulim, Bandar Bahru", "Kulim, Bandar Bahru", (5.36499, 100.56177)))
TIMEZONE = timezone("Asia/Kuala_Lumpur")
TIME_DATA_PATTERN = r"(\d+) (?:J|F|M|A|S|O|N|D).+?(\d+:\d\d).+?(\d+:\d\d).+?(\d+:\d\d).+?(\d+:\d\d).+?(\d+:\d\d).+?(\d+:\d\d).+?(\d+:\d\d)"


class Malaysia(Timetable):
    @classmethod
    def _lookupZone(cls, location):
        # Assume the earth is flat and coordinates are in a square grid, as the search area is relatively small?
        zoneOpts = ((((location[0] - zone.Location[0]) ** 2 + (location[1] - zone.Location[1]) ** 2), zone) for zone in ZONES)
        return min(zoneOpts)[1]

    @classmethod
    def CacheKey(cls, location, date):
        return cls._lookupZone(location).Code

    @classmethod
    def _mangleTime(cls, time_str, date):
        time = datetime.strptime(time_str, "%H:%M").time()
        dt = TIMEZONE.localize(datetime.combine(date, time))
        utc_dt = dt.astimezone(utc).replace(tzinfo=None)
        since_midnight = utc_dt - datetime.combine(date, datetime.min.time())
        return since_midnight.total_seconds() / 3600

    @classmethod
    def Times(cls, location, date):
        zone = cls._lookupZone(location)
        params = {
            "zone": zone.Code,
            "jenis": "year",
            "year": date.strftime("%Y"),
            "bulan": date.strftime("%m")
        }
        # This page contains an entire month's worth of data.
        # We only care about this specific day - we ignore the rest.
        # (could modify the caching to allow multiple returns, but no...)
        time_table = requests.get("http://www.e-solat.gov.my/web/muatturun.php", params=params)
        # Some zones return timestamps as "12.34" not "12:34".
        fixed_time_table_text = re.sub(r"([0-2]?\d)[:.]([0-6]\d)", r"\1:\2", time_table.text)
        for time_data in re.finditer(TIME_DATA_PATTERN, fixed_time_table_text, re.DOTALL):
            day, fajr, _, sunrise, dhuhr, asr, maghrib, isha = time_data.groups()
            if int(day) == date.day:
                return (zone.Name, {
                        "fajr": cls._mangleTime(fajr, date),
                        "sunrise": cls._mangleTime(sunrise, date),
                        "dhuhr": cls._mangleTime(dhuhr, date),
                        "asr": cls._mangleTime(asr, date),
                        "maghrib": cls._mangleTime(maghrib, date),
                        "isha": cls._mangleTime(isha, date),
                        }
                    )
        raise ValueError("No times returned")
