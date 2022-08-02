from flask import Flask, render_template, request, redirect, abort
from data import eventData
# from werkzeug.utils import secure_filename
# import os
# import base64

import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
import sys
import importlib
import pandas as pd
from random import randrange

from trees import tree_photos

# Add parent directory to PYTHONPATH to be able to find package.
file = Path(__file__).resolve()
parent, top = file.parent, file.parents[1] # 2

sys.path.append(str(top))
try:
    sys.path.remove(str(parent))
except ValueError:
    pass

__package__ = '.'.join(parent.parts[len(top.parts):])
importlib.import_module(__package__)

from tech_team_database.dependencies.DatabaseSQLOperations import TpSQL

application = Flask(__name__)

# application.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# application.config['MAX_CONTENT_PATH'] = 1024*1024*1024
# application.config['UPLOAD_PATH'] = 'static/uploads'
# application.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']

tpSQL = TpSQL(schema='tp2022')
data = {}

# login page
@application.route('/index')
@application.route('/')
def index():
    return render_template("login.html", error=False)

# event info form
@application.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        result = login(int(request.form['schoolid']), int(request.form['password']))
        if result == "ready":
            print(data)
            return render_template('form.html', data=data)
        elif result == "action":
           return render_template('login_error_action.html') 
        elif result == "wait":
            return render_template('login_error_wait.html')
        else:
            return render_template('login.html', error=True)
    return redirect('/')

# preview page
@application.route("/preview", methods=["GET", "POST"])
def preview():
    if request.method == "POST":
        global data
        data = process_data(request.form, request.files)
        print(data)
        return render_template("school_event.html", event=data, school=data['name'])
    return redirect('/')

# submitted page
@application.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        submit_to_database(data)
        return render_template("submit.html")
    return redirect('/')


# helper functions below:

def login(schoolid, password):
    table = tpSQL.getTable('event')
    if schoolid not in table['id'].values:
        return None
    if password == table.loc[table['id'] == schoolid]['pwd'].values[0]:
        scheduler_info = tpSQL.getTable('scheduler')
        scheduler_info = scheduler_info[scheduler_info['event_id'] == schoolid].iloc[0].to_dict()
        if not scheduler_info['submitted_tree_info'] and not scheduler_info['valid_species']:
            return 'action'
        elif scheduler_info['submitted_tree_info'] and not scheduler_info['valid_species']:
            return 'wait'

        global data
        data = table.set_index('id').T.to_dict()[schoolid]
        data['date'] = str(data['date']).split()[0]
        data['id'] = schoolid
        host_table = tpSQL.getTable('host')
        tree_table = tpSQL.getTable('tree')
        data['hosts'] = host_table[host_table['event_id'] == schoolid].to_dict('records')
        data['trees'] = []
        for host in data['hosts']:
            if type(host['photo_x']) == pd._libs.missing.NAType:
                host['photo_x'] = 0
            if type(host['photo_y']) == pd._libs.missing.NAType:
                host['photo_y'] = 0
            if type(host['photo_zoom']) == pd._libs.missing.NAType:
                host['photo_zoom'] = 100
        for index, row in tree_table.iterrows():
            if row['event_id'] == schoolid:
                tree_info = {'name' : row['species'], 'image_link' : tree_photos[row['species']]}
                data['trees'].append(tree_info)
        return 'ready'
    else:
        return None

def process_data(form, files):
    # print(form)
    # print(files)
    
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

    if form['is_pickup_only'] == 'True':
        data['is_pickup_only'] = True
    else:
        data['is_pickup_only'] = False

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
        host_exists = False
        for host in data['hosts']:
            if form['host' + str(i) + '_uuid'] != "" and host['uuid'] == int(form['host' + str(i) + '_uuid']):
                host_exists = True
                host['new'] = False
                host['bio'] = form['host' + str(i) + '_bio']
                host['photo'] = 'https://drive.google.com/uc?export=view&id=' + form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png'
                host['photo_x'] = form['host' + str(i) + '_photo_x']
                host['photo_y'] = form['host' + str(i) + '_photo_y']
                host['photo_zoom'] = form['host' + str(i) + '_photo_zoom']
        if not host_exists:
            data['hosts'].append({
                'new' : True,
                'uuid' : new_host_uuid(),
                'name' : form['host' + str(i) + '_name'],
                'bio' : form['host' + str(i) + '_bio'],
                'photo': 'https://drive.google.com/uc?export=view&id=' + form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png',
                'photo_x': form['host' + str(i) + '_photo_x'],
                'photo_y': form['host' + str(i) + '_photo_y'],
                'photo_zoom': form['host' + str(i) + '_photo_zoom'],
            })
        i += 1

    print(data)
    return data

def new_host_uuid():
    uuid = randrange(1000000000, 10000000000)
    uuid_list = tpSQL.getColData('host', ['uuid']).values
    while uuid in uuid_list:
        uuid = randrange(1000000000, 10000000000)
    return uuid

def submit_to_database(data):
    print(data)
    tpSQL.batchUpdate2('event', 'id', 
                        [[data['id'], data['name'], data['state'], data['date'], data['tree_goal'], data['media_type'] == 'Video', data['bio'], data['video'], data['display_email'], data['is_pickup_only']]], 
                        colLst=['id', 'name', 'state', 'date', 'tree_goal', 'media_type_video', 'bio', 'video', 'display_email', 'is_pickup_only'])

    # tpSQL.batchUpdate('school', 'id', 'date', [data['id']], [data['date']])

    # # hosts
    # for host in data['hosts']:
    #     if 'new' in host:
    #         if host['new'] == True:
    #             # get next uuid
    #             uuid = tpSQL.getColData('host', ['uuid']).max().values[0] + 1
    #             tpSQL.batchInsert('host', [[uuid, data['id'], host['name']]], cols=['uuid', 'event_id', 'name']) # need to add bio and photo, etc. 
    #         else:
    #             pass
    #             # tpSQL.batchUpdate('host', 'name') # better to check both name and event id, but need functionality from tpsql
    #     else: # host was in db before, but was deleted from form. Delete from db?
    #         pass

    # trees

    print(tpSQL.getTable('event'))

if __name__ == "__main__":
    application.run()

