from flask import Flask, redirect, request
from models import User
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
    async_geocode_pool.submit(async_geocode, user)
    Timeline.push_pins_for_user(user)
    return ""

@app.route('/')
def index():
    return "marhaba!"
    return redirect('https://apps.getpebble.com/applications/53ab84141d576ea3c30000d6')

if __name__ == '__main__':
    app.run(debug=True)
