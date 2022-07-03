from flask import Flask, render_template, request, redirect, abort
from data import eventData
from werkzeug.utils import secure_filename
import os
import base64

import datetime
from dateutil.relativedelta import relativedelta

application = Flask(__name__)

application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
application.config['MAX_CONTENT_PATH'] = 1024*1024*1024
application.config['UPLOAD_PATH'] = 'static/uploads'
application.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']


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
        data = process_data(request.form, request.files)
        print(data)
        return render_template("school_event.html", event=data, school=data['name'])
    else:
        return redirect('/')

def process_data(form, files):
    print(form)
    # print(files)
    
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
    if 'youtu.be' in data['video']:
        data['video'] = "https://www.youtube.com/embed/" + data['video'].split('.be/',1)[1].split('&')[0]
    elif 'youtube.com/watch?' in data['video']:
        data['video'] = "https://www.youtube.com/embed/" + data['video'].split('/watch?v=',1)[1].split('&')[0]
    elif 'drive.google.com' in data['video']:
        data['video'] = data['video'].replace('view','preview')


    data['display_email'] = form['display_email']

    if form['pickup_only'] == 'True':
        data['pickup_only'] = True
    else:
        data['pickup_only'] = False

    data['hosts'] = []
    i = 1
    while 'host' + str(i) + '_name' in form:
        # 1) save photo file
        # f = request.files['host' + str(i) + '_photo']
        # filename = secure_filename(f.filename)
        # if filename != '':
        #     file_ext = os.path.splitext(filename)[1]
        #     if file_ext not in application.config['UPLOAD_EXTENSIONS']:
        #         abort(400)
        #     f.save(os.path.join(application.config['UPLOAD_PATH'], filename))

        # 2) use decoded image data directly
        # data['hosts'].append({
        #     'name' : form['host' + str(i) + '_name'],
        #     'bio' : form['host' + str(i) + '_bio'],
        #     'photo': 'data:image/jpeg;base64,' + base64.b64encode(files['host' + str(i) + '_photo'].read()).decode() if files['host' + str(i) + '_photo'].filename != '' else 'static/images/default_profile.png'
        #     # 'photo' : 'static/uploads/' + filename if filename != '' else 'static/images/default_profile.png'
        # })

        # 3) google drive link
        data['hosts'].append({
            'name' : form['host' + str(i) + '_name'],
            'bio' : form['host' + str(i) + '_bio'],
            'photo': form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png',
            'photo_x': form['host' + str(i) + '_photo_x'],
            'photo_y': form['host' + str(i) + '_photo_y'],
            'photo_zoom': form['host' + str(i) + '_photo_zoom'],
        })
        i += 1

    data['trees'] = []
    i = 1
    while 'tree' + str(i) + '_species' in form:
        data['trees'].append({
            'name' : form['tree' + str(i) + '_species'],
            'image_link' : 'static/images/default_tree.png',
            'description_link': ''
        })
        i += 1

    print(data)
    return data


if __name__ == "__main__":
    application.run()

