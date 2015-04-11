from flask import Flask, redirect, request, render_template
from models import User
from praytimes import PrayTimes
from timeline import Timeline
from datetime import datetime
import concurrent.futures

app = Flask(__name__)

async_geocode_pool = concurrent.futures.ThreadPoolExecutor(max_workers=5)
def async_geocode(user):
    user.geocode()
    user.save()

@app.route('/subscribe', methods=["POST"])
def subscribe():
    data = request.get_json()
    user_token = data["user_token"]
    try:
        user = User.objects.get(user_token=user_token)
    except User.DoesNotExist:
        user = User(user_token=user_token)
        user.created_at = datetime.utcnow()
    user.timeline_token = data["timeline_token"]
    user.location = [float(data["location_lat"]), float(data["location_lon"])]
    user.subscribed_at = datetime.utcnow()
    user.save()
    def geocode_callback(future):
        print("Geocode callback OK!")
        Timeline.push_pins_for_user(user)
    async_geocode_pool.submit(async_geocode, user).add_done_callback(geocode_callback)
    return ""

@app.route('/settings/<user_token>',  methods=["GET", "POST"])
def settings(user_token):
    try:
        user = User.objects.get(user_token=user_token)
    except User.DoesNotExist:
        return render_template('registration_wait.html')

    # Wait until geocode completes
    if not user.location_geoname:
        return render_template('registration_wait.html')

    if request.method == "POST":
        user.config["method"] = request.form["method"]
        user.config["asr"] = request.form["asr"]
        user.save()
        Timeline.push_pins_for_user(user)
        return render_template('settings_confirmed.html')

    asr_options = ["Standard", "Hanafi"]
    method_options = list(PrayTimes.methods.keys())
    return render_template('settings.html', config=user.config, location=user.location_geoname, asr_options=asr_options, method_options=method_options)

@app.route('/')
def index():
    return "marhaba!"
    return redirect('https://apps.getpebble.com/applications/53ab84141d576ea3c30000d6')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
