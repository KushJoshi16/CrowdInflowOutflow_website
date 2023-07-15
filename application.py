from flask import (
    Flask, 
    jsonify, 
    request, 
    Response, 
    redirect,
    abort, 
    g,
    render_template,
    session,
    url_for,
    flash
)
import shutil
import pandas as pd
from pathlib import Path
from VideoAnalyser.VideoAnalyser import Analyser
import json
import logging
import os
from flask_cors import CORS


class User:

    def __init__(self, id, username, password) -> None:
        self.id = id
        self.username = username
        self.password = password
        
    def __repr__(self) -> str:
        return f'<User : {self.username}>'

admins = []
admins.append(User(id=1,username='admin',password='admin'))
admins.append(User(id=2,username='admin1',password='admin1'))


logger = logging.getLogger('azure.mgmt.resource')
va = Analyser()

application = Flask(__name__)
application.secret_key = 'MYsecretKEy'
CORS(application)
app = application

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
       user = [x for x in admins if x.id == session['user_id']]
       if user:
           g.user = user[0]


@app.route('/')
def index():
    if not g.user:
        return redirect(url_for('login'))
    path = Path('./static/videos/output.mp4')
    if path.is_file():
        return render_template('index.html',OUT_FILE_USE_STATUS = va.OUT_FILE_IN_USE)
    else:
        flash('No Output Video File! Please Analyse a video first')
        return redirect(url_for('admin'))


@app.route('/admin')
def admin():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('admin_page.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method =='POST':
        session.pop('user_id',None)

        username = request.form["username"]
        password = request.form["password"]

        user = [x for x in admins if x.username == username]
        if user and user[0].password == password:
            session['user_id'] = user[0].id
            flash('You were successfully logged in')
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials')
        return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id',None)
    if not g.user:
        return redirect(url_for('login'))
    else:
        g.user = None
    flash('You have successfully logged yourself out.')
    return redirect(url_for('login'))


@app.route('/setinputData',methods=['POST'])
def setinputData():
    filepath = None
    if 'file' not in request.files:
        
        flash('Error')
        return redirect(url_for('admin'))
    
    f = request.files['file']
    basepath = os.path.dirname(__file__)
    filepath = os.path.join(basepath,'uploads',"input.mp4")
    f.save(filepath)
    logger.info("Input data received")
    try:
        src = "uploads"
        trg = "assets"
        
        files=os.listdir(src)
        # for fname in files:
        shutil.copy2(os.path.join(src,"input.mp4"), trg)
        
        logger.info("Input data stored in assets")

        flash('Input Saved')
        return redirect(url_for('admin'))
    except Exception as e:
        logger.error(e)
        flash('Error')
        return redirect(url_for('admin'))
 
@app.route('/analyseVideo')
def analysevideo():
    path = Path('./assets/input.mp4')
    if path.is_file():
        try:
            flash('Analyser Started')
            va.Analyser()
            logger.info("Analyser Started")
            flash('Analysis Completed')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(e)
            return e
    else:
        flash('No Input Data! Please upload input data first')
        return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)