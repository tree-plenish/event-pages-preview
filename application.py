import copy
from flask import Flask, render_template, request, redirect
import pandas as pd
from os import path
import pickle
from data import eventData

application = Flask(__name__)

application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

#home page
@application.route('/index')
@application.route('/')
def index():
    return render_template("form.html")

#school-specific page router
@application.route('/school')
def school():
    return render_template('school_event.html', event=eventData, school=eventData['name'])

@application.route("/preview", methods=["GET", "POST"])
def preview():
    if request.method == "POST":
        print(request.form)
        return render_template("test.html", data=request.form)

if __name__ == "__main__":
    application.run()

