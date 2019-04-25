'''
== Web app main entrance ==

Finished on Aug 10, 2017
@author: James Lu
'''

import os
import datetime
import time
import flask_login
from evid_study import app, progress_manager
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash, g


# Parameters
inactive_session_expire_time = 5            # in min
force_rest_time = 40                        # in min


# Logout after 5 min inactive
@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=inactive_session_expire_time)
    session.modified = True


@app.route('/')
def index():
    if 'logged_in' in session:
        if session['logged_in'] == True:
            return redirect(url_for('showEvent'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] not in app.config['USERBOOK']:
            error = 'Invalid username or password.'
        elif request.form['password'] != app.config['USERBOOK'][request.form['username']]:
            error = 'Invalid username or password.'
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            session['start_time'] = time.time()
            #flash('Log in success.')
            if not progress_manager.initialize():
                return redirect(url_for('logout'))
            progress_manager.writeLogin()
            return redirect(url_for('showEvent'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    if progress_manager.initialize():
        progress_manager.writeLogout()
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You were logged out.')
    return redirect(url_for('login'))


import evid_study.show_event
import evid_study.show_question
import evid_study.inspect_question
