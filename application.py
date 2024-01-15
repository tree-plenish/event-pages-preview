from flask import Flask, render_template, request, redirect, session, send_file
from flask_session import Session

import shutil
import tempfile
import weakref

import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from pathlib import Path
import sys
import os
import importlib
import pandas as pd
from random import randrange
import uuid
from xhtml2pdf import pisa
import base64

# Add parent directory to PYTHONPATH to be able to find package.
file = Path(__file__).resolve()
parent, top = file.parent, file.parents[1] # 2
sys.path.append(str(top))

__package__ = '.'.join(parent.parts[len(top.parts):])
importlib.import_module(__package__)

from tech_team_database.dependencies.DatabaseSQLOperations import TpSQL

application = Flask(__name__)
application.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
application.config['SESSION_TYPE'] = 'filesystem'
application.config['SESSION_PERMANENT'] = False
application.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)


application.config.from_object(__name__)
Session(application)

tpSQL = TpSQL(schema='tp2023')

class FileRemover(object):
    def __init__(self):
        self.weak_references = dict()  # weak_ref -> filepath to remove

    def cleanup_once_done(self, response, filepath):
        wr = weakref.ref(response, self._do_cleanup)
        self.weak_references[wr] = filepath

    def _do_cleanup(self, wr):
        filepath = self.weak_references[wr]
        print('Deleting %s' % filepath)
        shutil.rmtree(filepath, ignore_errors=True)
file_remover = FileRemover()

# login page
@application.route('/index')
@application.route('/')
def index():
    return render_template("login.html", error=False)

# form
@application.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST" and request.form:
        if not request.form['password'].isdigit():
            return render_template('login.html', error=True)
        result = login(int(request.form['schoolid']), int(request.form['password']), request.form['function'])
        if result == "ready":
            return render_template(f'{session.get("function")}/form.html', data=session.get('data'))
        elif result == "action":
           return render_template('login_error_action.html') 
        elif result == "wait":
            return render_template('login_error_wait.html')
        else:
            return render_template('login.html', error=True)
    elif request.method == "POST":
        return render_template(f'{session.get("function")}/form.html', data=session.get('data'))
    return redirect('/')

# preview page (event-page)
@application.route("/preview", methods=["GET", "POST"])
def preview():
    if request.method == "POST" and session.get('function') == 'event-page':
        session['data'] = process_data(request.form, request.files)
        return render_template(f"{session.get('function')}/preview.html", event=session.get('data'), school=session.get('data')['name'])
    return redirect('/')

# submitted page (event-page)
@application.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST" and session.get('function') == 'event-page':
        submit_to_database(session.get('data'))
        return render_template("event-page/submit.html")
    return redirect('/')

# download as pdf (press-release)
@application.route("/download_pdf", methods=["GET", "POST"])
def download_pdf():
    if request.method == "POST" and session.get('function') == 'press-release':
        session['data'] = process_data(request.form, request.files)
        tempdir = tempfile.mkdtemp()
        convert_html_to_pdf(write_press_release(session.get('data')), f'{tempdir}/press_release.pdf')
        response = send_file(f'{tempdir}/press_release.pdf', as_attachment=True)
        file_remover.cleanup_once_done(response, tempdir)
        return response
    return redirect('/')

# helper functions below:

def login(schoolid, password, function):
    table = tpSQL.getTable('event').fillna(0).replace(['nan'], [''])
    tree_table = tpSQL.getTable('tree')
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
        data['trees'] = []
        for index, row in tree_table.iterrows():
            if row['event_id'] == schoolid:
                tree_info = {'name' : row['species'], 'image_link' : treeInfo[treeInfo['species'] == row['species']]['image_link'].values[0]}
                data['trees'].append(tree_info)
        
        if function == 'event-page':
            data['display_video'] = data['video']
            data['id'] = schoolid
            host_table = tpSQL.getTable('host')
            data['hosts'] = host_table[host_table['event_id'] == schoolid].to_dict('records')
            
            for host in data['hosts']:
                host['display'] = True
                if host['photo'] == 'static/images/default_profile.png':
                    host['form_photo'] = ''
                elif 'https://drive.google.com/thumbnail?export=view&id=' in host['photo']:
                    host['form_photo'] = host['photo'].split('https://drive.google.com/thumbnail?export=view&id=')[1]
                if type(host['photo_x']) == pd._libs.missing.NAType:
                    host['photo_x'] = 0
                if type(host['photo_y']) == pd._libs.missing.NAType:
                    host['photo_y'] = 0
                if type(host['photo_zoom']) == pd._libs.missing.NAType:
                    host['photo_zoom'] = 100
            # make primary host first host
            # for i, host in enumerate(data['hosts']):
            #     if host['is_primary']:
            #         data['hosts'].insert(0, data['hosts'].pop(i))
            #         break
            print(data['hosts'])
        else:
            data['pr_date'] = datetime.date.today()

        session['data'] = data
        session['function'] = function # event-page or press-release

        return 'ready'
    else:
        return None

@application.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

def process_data(form, files):
    print(form)
    
    data = session.get('data')
    data['name'] = form['name']
    data['state'] = form['state']

    date = datetime.datetime.strptime(form['date'], '%Y-%m-%d').date()
    date_minus_month =  date - relativedelta(months=1)
    data['order_deadline'] = date_minus_month.strftime('%B %d, %Y').replace(" 0", " ")
    data['form_date'] = form['date']
    data['date'] = date.strftime('%B %d, %Y').replace(" 0", " ")
    
    data['tree_goal'] = int(form['tree_goal'])

    if session.get('function') == 'event-page':
        data['media_type_video'] = True if form['media_type'] == "Video" else False
        data['bio'] = form['bio']
        data['display_video'] = form['video']
        if 'youtu.be' in data['display_video']:
            data['video'] = "https://www.youtube.com/embed/" + data['display_video'].split('.be/',1)[1].split('&')[0]
        elif 'youtube.com/watch?' in data['display_video']:
            data['video'] = "https://www.youtube.com/embed/" + data['display_video'].split('/watch?v=',1)[1].split('&')[0]
        elif 'drive.google.com' in data['display_video']:
            data['video'] = data['display_video'].replace('view','preview')


        data['display_email'] = form['display_email']

        if form['is_pickup_only'] == 'True':
            data['is_pickup_only'] = True
        else:
            data['is_pickup_only'] = False


        for host in data['hosts']:
            host['display'] = False
        i = 1
        while 'host' + str(i) + '_name' in form:
            host_exists = False
            for host in data['hosts']:
                if form['host' + str(i) + '_uuid'] != "" and host['uuid'] == form['host' + str(i) + '_uuid']:
                    host_exists = True
                    host['display'] = True
                    host['name'] = form['host' + str(i) + '_name']
                    host['bio'] = form['host' + str(i) + '_bio']
                    host['form_photo'] = form['host' + str(i) + '_photo']
                    host['photo'] = 'https://drive.google.com/thumbnail?export=view&id=' + form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png'
                    host['photo_x'] = form['host' + str(i) + '_photo_x'] if form['host' + str(i) + '_photo'] != '' else 0
                    host['photo_y'] = form['host' + str(i) + '_photo_y'] if form['host' + str(i) + '_photo'] != '' else 0
                    host['photo_zoom'] = form['host' + str(i) + '_photo_zoom'] if form['host' + str(i) + '_photo'] != '' else 100
                    host['primary'] = (i == 1)
            if not host_exists:
                data['hosts'].append({
                    'display' : True,
                    'uuid' : new_host_uuid(),
                    'name' : form['host' + str(i) + '_name'],
                    'bio' : form['host' + str(i) + '_bio'],
                    'form_photo' : form['host' + str(i) + '_photo'],
                    'photo': 'https://drive.google.com/thumbnail?export=view&id=' + form['host' + str(i) + '_photo'] if form['host' + str(i) + '_photo'] != '' else 'static/images/default_profile.png',
                    'photo_x': form['host' + str(i) + '_photo_x'],
                    'photo_y': form['host' + str(i) + '_photo_y'],
                    'photo_zoom': form['host' + str(i) + '_photo_zoom'],
                    'primary' : i == 1
                })
            i += 1
        
        # reorder uuids to keep host order
        print(data['hosts'])
        uuids = [host['uuid'] for host in data['hosts']]
        uuids.sort()
        for i, host in enumerate(data['hosts']):
            host['uuid'] = uuids[i]

    else: # session.get('function') == 'press-release':
        data['town'] = form['town']
        data['quote'] = form['quote']
        data['pr_date'] = datetime.datetime.strptime(form['pr_date'], '%Y-%m-%d').date().strftime('%B %d, %Y').replace(" 0", " ")

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
        [[data['id'], data['name'], data['state'], data['media_type_video'], data['bio'], data['video'], data['display_email'], data['is_pickup_only']]], 
        colLst=['id', 'name', 'state', 'media_type_video', 'bio', 'video', 'display_email', 'is_pickup_only'])

    existing_host_uuids = tpSQL.getColData('host', ['uuid']).values

    for host in data['hosts']:
        if 'display' in host and host['display']:
            if host['uuid'] not in existing_host_uuids:
                tpSQL.batchInsert('host', 
                    [[host['uuid'], data['id'], host['primary'], host['name'], host['bio'], host['photo'], int(host['photo_x']), int(host['photo_y']), int(host['photo_zoom'])]], 
                    colLst=['uuid', 'event_id', 'is_primary', 'name', 'bio', 'photo', 'photo_x', 'photo_y', 'photo_zoom']) 
            else:
                tpSQL.batchUpdate2('host', 'uuid', 
                    [[host['uuid'], data['id'], host['primary'], host['name'], host['bio'], host['photo'], int(host['photo_x']), int(host['photo_y']), int(host['photo_zoom'])]], 
                    colLst=['uuid', 'event_id', 'is_primary', 'name', 'bio', 'photo', 'photo_x', 'photo_y', 'photo_zoom']) 
        else: 
            # host was in db before, but was deleted from form. Delete from db
            tpSQL.host_tbl_delete_row(host['uuid'])
            pass

    tpSQL.batchUpdate2('scheduler', 'event_id',
                    [[data['id'], True]], 
                    colLst=['event_id', 'submitted_epf']) 
    
    # print(tpSQL.getTable('event'))

def write_press_release(data):
    print(data)
    species = [t['name'] for t in data['trees']]
    
    if len(species) == 1:
        species_string = species[0]
    elif len(species) == 2:
        species_string = species[0] + ' and ' + species[1]
    else:
        species_string = ', '.join(species[:-1]) + ', and ' + species[-1]

    with open("static/images/favicon.png", "rb") as f:
        logo_binary = base64.b64encode(f.read())

    return f'''
    <html>
    <head>
    <style>
    body{{
        font-size: 1.5em;
        font-family: serif;
        margin: 40px;
    }}
    </style>
    </head>
    <body>
    <table>
    <tr>
        <td width=50%><img src="data:image/gif;base64,{logo_binary}" width=120px height=120px style="float:left"></td>
        <td width=50%><p style="text-align:right">Caroline Sprenkle<br>
        Media Relations<br>
        marketing@tree-plenish.org</td></p>
    </tr>
    </table>
        <h1>
        {data['name']} Students Partner with Tree-Plenish to Offset Their School’s Energy Consumption 
        by Planting Saplings
        </h1>
        <h3 style="font-style: italic">
        Calling {data['town']} residents to action
        </h3>
        <p>
        {data['town'].upper()}, {data['state']} ({data['pr_date']}) -- This year, students from 
        {data['name']} are partnering with the nonprofit <a href="https://www.tree-plenish.org/">Tree-Plenish</a> to help make their 
        community more sustainable. They plan to plant {data['tree_goal']} saplings on {data['date']} 
        to offset their school’s energy consumption from the past academic year.
        </p>
        <p>
        Tree-Plenish mentors students through a step-by-step process to achieve their ultimate goal: 
        hosting their own tree-planting event to help offset the carbon their school emits in an academic 
        year. With the help of Tree-Plenish, students calculate their school’s energy consumption to 
        determine their sapling goal. In order to reach their goal number of saplings, students rely on 
        residents of the community to order saplings to be planted by volunteers in their yard.
        </p>
        <p>
        Throughout the fall and early winter, students from {data['name']} have been planning their 
        tree-planting event. They are now starting to market their event to the community, with the 
        goal of getting residents to order a sapling to be planted in their yard on the day of the event. 
        Students will also reach out to their community to recruit volunteers to help plant saplings on 
        the day of the event. These events are a perfect opportunity for members of the community to connect 
        with each other and think about sustainability in their community. 
        </p>
        <p>
        Residents of the community are able to help support the event starting now! They can order a sapling 
        to be planted in their yard or sign up to volunteer to plant saplings on the day of the event. Saplings 
        are ${data['current_tree_price']} and residents can choose between {species_string} saplings. The more residents 
        that request saplings, the faster the students are able to reach their goal. If residents are unable to 
        order a sapling or volunteer their time, they can also make a monetary contribution on the Tree-Plenish 
        website to help support future tree-planting events.
        </p>
        <p>
        {data['quote']}
        </p>
        <p>
        Tree-Plenish is a student-led 501(c)(3) non profit organization with the mission of empowering students 
        to create a more sustainable and equitable future through community tree-planting. Together with students 
        from {data['name']}, Tree-Plenish hopes to drive {data['town']} towards a sustainable future. 
        </p >
    </body
    </html>
        '''


def convert_html_to_pdf(source_html, output_filename):
    result_file = open(output_filename, "w+b")
    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
            source_html,
            dest=result_file)
    result_file.close()

    # return False on success and True on errors
    return pisa_status.err

if __name__ == "__main__":
    application.run()