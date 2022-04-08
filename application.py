from flask import Flask, render_template, request, redirect
from data import eventData

import datetime
from dateutil.relativedelta import relativedelta

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
        data = process_data(request.form)
        return render_template("school_event.html", event=data, school=data['name'])
    else:
        return redirect('/')

def process_data(form):
    data = {}
    data['name'] = form['name']
    data['state'] = form['state']

    date = datetime.datetime.strptime(form['date'], '%Y-%m-%d').date()
    date_minus_month =  date - relativedelta(months=1)
    data['order_deadline'] = date_minus_month.strftime('%B %d, %Y').replace(" 0", " ")
    data['date'] = date.strftime('%B %d, %Y').replace(" 0", " ")
    
    data['tree_goal'] = int(form['tree_goal'])
    data['media_type'] = form['media_type']
    data['text'] = form['text']
    data['video'] = form['video']
    data['display_email'] = form['display_email']

    if form['pickup_only'] == 'True':
        data['pickup_only'] = True
    else:
        data['pickup_only'] = False

    data['hosts'] = []
    i = 1
    while 'host' + str(i) + '_name' in form:
        data['hosts'].append({
            'name' : form['host' + str(i) + '_name'],
            'bio' : form['host' + str(i) + '_bio'],
            'photo' : form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png'
        })
        i += 1

    return data


if __name__ == "__main__":
    application.run()

