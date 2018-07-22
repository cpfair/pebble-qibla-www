from flask import Flask, redirect, request, render_template, jsonify
from models import User
from timetable import TimetableResolver
from timeline import Timeline
from datetime import datetime
import logging
import json
from raven.contrib.flask import Sentry

app = Flask(__name__)

sentry = Sentry(app, logging=True, level=logging.ERROR)

@app.route('/settings/<user_token>',  methods=["GET", "POST"])
def settings(user_token):
    return render_template('timeline_shutdown.html')

@app.route('/')
def index():
    return "marhaba!"
    return redirect('https://apps.getpebble.com/applications/53ab84141d576ea3c30000d6')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
