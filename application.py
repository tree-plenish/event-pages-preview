from flask import Flask, render_template, request, redirect, session

import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
import sys
import os
import importlib
import pandas as pd
from random import randrange
import uuid

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
application.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

tpSQL = TpSQL(schema='tp2022')

# login page
@application.route('/index')
@application.route('/')
def index():
    return render_template("login.html", error=False)

# event info form
@application.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST" and request.form:
        result = login(int(request.form['schoolid']), int(request.form['password']))
        if result == "ready":
            # print(session.get('data'))
            return render_template('form.html', data=session.get('data'))
        elif result == "action":
           return render_template('login_error_action.html') 
        elif result == "wait":
            return render_template('login_error_wait.html')
        else:
            return render_template('login.html', error=True)
    elif request.method == "POST":
        return render_template('form.html', data=session.get('data'))
    return redirect('/')

# preview page
@application.route("/preview", methods=["GET", "POST"])
def preview():
    if request.method == "POST":
        session['data'] = process_data(request.form, request.files)
        # print(session.get('data'))
        return render_template("school_event.html", event=session.get('data'), school=session.get('data')['name'])
    return redirect('/')

# submitted page
@application.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        submit_to_database(session.get('data'))
        return render_template("submit.html")
    return redirect('/')


# helper functions below:

def login(schoolid, password):
    table = tpSQL.getTable('event').fillna(0).replace(['nan'], [''])
    treeInfo = tpSQL.getTable('tree_info')
    if schoolid not in table['id'].values:
        return None
    if password == table.loc[table['id'] == schoolid]['pwd'].values[0]:
        scheduler_info = tpSQL.getTable('scheduler')
        scheduler_info = scheduler_info[scheduler_info['event_id'] == schoolid].iloc[0].to_dict()
        if not scheduler_info['submitted_tree_info'] and not scheduler_info['valid_species']:
            return 'action'
        elif scheduler_info['submitted_tree_info'] and not scheduler_info['valid_species']:
            return 'wait'

        data = table.set_index('id').T.to_dict()[schoolid]
        data['form_date'] = str(data['date']).split()[0]
        data['display_video'] = data['video']
        data['id'] = schoolid
        host_table = tpSQL.getTable('host')
        tree_table = tpSQL.getTable('tree')
        data['hosts'] = host_table[host_table['event_id'] == schoolid].to_dict('records')
        data['trees'] = []
        for host in data['hosts']:
            if host['photo'] == 'static/images/default_profile.png':
                host['form_photo'] = ''
            elif 'https://drive.google.com/uc?export=view&id=' in host['photo']:
                host['form_photo'] = host['photo'].split('https://drive.google.com/uc?export=view&id=')[1]
            if type(host['photo_x']) == pd._libs.missing.NAType:
                host['photo_x'] = 0
            if type(host['photo_y']) == pd._libs.missing.NAType:
                host['photo_y'] = 0
            if type(host['photo_zoom']) == pd._libs.missing.NAType:
                host['photo_zoom'] = 100
        for index, row in tree_table.iterrows():
            if row['event_id'] == schoolid:
                tree_info = {'name' : row['species'], 'image_link' : treeInfo[treeInfo['species'] == row['species']]['image_link'].values[0]}
                data['trees'].append(tree_info)
        session['data'] = data
        return 'ready'
    else:
        return None

def process_data(form, files):
    # print(form)
    # print(files)
    data = session.get('data')
    data['name'] = form['name']
    data['state'] = form['state']

    date = datetime.datetime.strptime(form['date'], '%Y-%m-%d').date()
    date_minus_month =  date - relativedelta(months=1)
    data['order_deadline'] = date_minus_month.strftime('%B %d, %Y').replace(" 0", " ")
    data['form_date'] = form['date']
    data['date'] = date.strftime('%B %d, %Y').replace(" 0", " ")
    
    data['tree_goal'] = int(form['tree_goal'])
    data['media_type'] = form['media_type']
    data['text'] = form['text']
    data['display_video'] = form['video']
    if 'youtu.be' in data['video']:
        data['video'] = "https://www.youtube.com/embed/" + data['display_video'].split('.be/',1)[1].split('&')[0]
    elif 'youtube.com/watch?' in data['video']:
        data['video'] = "https://www.youtube.com/embed/" + data['display_video'].split('/watch?v=',1)[1].split('&')[0]
    elif 'drive.google.com' in data['video']:
        data['video'] = data['display_video'].replace('view','preview')


    data['display_email'] = form['display_email']

    if form['is_pickup_only'] == 'True':
        data['is_pickup_only'] = True
    else:
        data['is_pickup_only'] = False

    i = 1
    while 'host' + str(i) + '_name' in form:
        host_exists = False
        for host in data['hosts']:
            if form['host' + str(i) + '_uuid'] != "" and host['uuid'] == form['host' + str(i) + '_uuid']:
                host_exists = True
                host['new'] = host['new'] if 'new' in host else False
                host['bio'] = form['host' + str(i) + '_bio']
                host['form_photo'] = form['host' + str(i) + '_photo']
                host['photo'] = 'https://drive.google.com/uc?export=view&id=' + form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png'
                host['photo_x'] = form['host' + str(i) + '_photo_x']
                host['photo_y'] = form['host' + str(i) + '_photo_y']
                host['photo_zoom'] = form['host' + str(i) + '_photo_zoom']
                # host['primary'] = (i == 1)
        if not host_exists:
            data['hosts'].append({
                'new' : True,
                'uuid' : new_host_uuid(),
                'name' : form['host' + str(i) + '_name'],
                'bio' : form['host' + str(i) + '_bio'],
                'form_photo' : form['host' + str(i) + '_photo'],
                'photo': 'https://drive.google.com/uc?export=view&id=' + form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png',
                'photo_x': form['host' + str(i) + '_photo_x'],
                'photo_y': form['host' + str(i) + '_photo_y'],
                'photo_zoom': form['host' + str(i) + '_photo_zoom']
                # 'primary' : i == 1
            })
        i += 1

    return data

def new_host_uuid():
    new_uuid = str(uuid.uuid4())
    uuid_list = tpSQL.getColData('host', ['uuid']).values
    while uuid in uuid_list:
        new_uuid = str(uuid.uuid4())
    return new_uuid

def submit_to_database(data):
    print(data)
    tpSQL.batchUpdate2('event', 'id', 
        [[data['id'], data['name'], data['state'], data['date'], data['tree_goal'], data['media_type'] == 'Video', data['bio'], data['video'], data['display_email'], data['is_pickup_only']]], 
        colLst=['id', 'name', 'state', 'date', 'tree_goal', 'media_type_video', 'bio', 'video', 'display_email', 'is_pickup_only'])

    for host in data['hosts']:
        if 'new' in host:
            if host['new'] == True:
                tpSQL.batchInsert('host', 
                    [[host['uuid'], data['id'], host['name'], host['bio'], host['photo'], int(host['photo_x']), int(host['photo_y']), int(host['photo_zoom'])]], 
                    colLst=['uuid', 'event_id', 'name', 'bio', 'photo', 'photo_x', 'photo_y', 'photo_zoom']) 
            else:
                tpSQL.batchUpdate2('host', 'uuid', 
                    [[host['uuid'], data['id'], host['name'], host['bio'], host['photo'], int(host['photo_x']), int(host['photo_y']), int(host['photo_zoom'])]], 
                    colLst=['uuid', 'event_id', 'name', 'bio', 'photo', 'photo_x', 'photo_y', 'photo_zoom']) 
        else: 
            # host was in db before, but was deleted from form. Delete from db
            tpSQL.host_tbl_delete_row(host['uuid'])
            pass

    tpSQL.batchUpdate2('scheduler', 'event_id',
                    [[1000, True]], 
                    colLst=['event_id', 'submitted_epf']) 
    
    print(tpSQL.getTable('event'))
    print(tpSQL.getTable('host'))

if __name__ == "__main__":
    application.run()

