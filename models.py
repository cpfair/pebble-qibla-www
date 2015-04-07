import mongoengine as me
import os

class User(me.Document):
    user_token = me.StringField()
    timeline_token = me.StringField()
    location = me.PointField()
    location_geoname = me.StringField()
    created_at = me.DateTimeField()
    subscribed_at = me.DateTimeField()

    def geocode(self):
        import requests
        res = requests.get('http://api.geonames.org/findNearbyPlaceNameJSON', params={'lat': self.location[0], 'lng': self.location[1], 'maxRows': 1, 'username': os.environ.get('GEONAMES_USERNAME', 'demo')})
        for place in res.json()["geonames"]:
            self.location_geoname = place["name"]

me.connect('qibla')
