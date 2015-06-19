from flask import Flask, redirect, request, render_template, jsonify
from models import User
from praytimes import PrayTimes
from timeline import Timeline
from datetime import datetime
import concurrent.futures
import logging
from raven.contrib.flask import Sentry

app = Flask(__name__)

sentry = Sentry(app, logging=True, level=logging.ERROR)

@app.route('/subscribe', methods=["POST"])
def subscribe():
    newrelic.agent.add_custom_parameter('request_body', request.get_json())
    data = request.get_json()
    user_token = data["user_token"]
    try:
        user = User.objects.get(user_token=user_token)
    except User.DoesNotExist:
        user = User(user_token=user_token)
        user.created_at = datetime.utcnow()
    if "timeline_token" in data:
        user.timeline_token = data["timeline_token"]
    user.location = [float(data["location_lat"]), float(data["location_lon"])]
    user.tz_offset = int(data["tz_offset"])
    user.subscribed_at = datetime.utcnow()
    user.geocode()
    user.save()
    Timeline.push_pins_for_user(user)

    result = {"location_geoname": user.location_geoname}
    return jsonify(result)

@app.route('/settings/<user_token>',  methods=["GET", "POST"])
def settings(user_token):
    try:
        user = User.objects.get(user_token=user_token)
    except User.DoesNotExist:
        return render_template('registration_wait.html')

    # Wait until geocode completes
    if not user.location_geoname:
        return render_template('registration_wait.html')

    if not user.timeline_token:
        return render_template('no_timeline.html')

    if request.method == "POST":
        old_config = dict(user.config)
        user.config["method"] = request.form["method"]
        user.config["asr"] = request.form["asr"]
        user.save()
        if old_config != user.config:
            Timeline.push_pins_for_user(user)
        return render_template('settings_confirmed.html')

    asr_options = ["Standard", "Hanafi"]
    method_options = list(PrayTimes.methods.keys())
    return render_template('settings.html', user=user, asr_options=asr_options, method_options=method_options)

@app.route('/')
def index():
    return "marhaba!"
    return redirect('https://apps.getpebble.com/applications/53ab84141d576ea3c30000d6')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
