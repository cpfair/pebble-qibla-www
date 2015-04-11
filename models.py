import mongoengine as me
import os

class User(me.Document):
    DEFAULT_CONFIG = {
        "method": "ISNA",
        "asr": "Standard"
    }
    user_token = me.StringField()
    timeline_token = me.StringField()
    location = me.PointField()
    location_geoname = me.StringField()
    created_at = me.DateTimeField()
    subscribed_at = me.DateTimeField()
    # It melted down when I tried name the db field "config"
    # Not sure what was up
    _sparse_config = me.DictField(db_field="sparse_config")

    def geocode(self):
        import requests
        res = requests.get('http://api.geonames.org/findNearbyPlaceNameJSON', params={'lat': self.location[0], 'lng': self.location[1], 'maxRows': 1, 'username': os.environ.get('GEONAMES_USERNAME', 'demo')})
        for place in res.json()["geonames"]:
            self.location_geoname = place["name"]

    @property
    def config(self):
        if not hasattr(self, "_config_inst"):
            self._config_inst = dict(self.DEFAULT_CONFIG)
            self._config_inst.update(self._sparse_config)
        return self._config_inst

    def save(self):
        # Paste _config_inst back into _sparse_config if reqd.
        if hasattr(self, "_config_inst"):
            # Transfer updated keys if not default
            for k,v in self._config_inst.items():
                if self.DEFAULT_CONFIG[k] != v:
                    self._sparse_config[k] = v
                elif k in self._sparse_config:
                    del self._sparse_config[k]
            # Remove deleted keys
            for k,v in self.DEFAULT_CONFIG.items():
                if k not in self._config_inst and k in self._sparse_config:
                    del self._sparse_config[k]
        super(User, self).save()

me.connect('qibla')
