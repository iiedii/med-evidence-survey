import os
import time
from evid_study import app, progress_manager
from flask import Flask, request, session, redirect, url_for, abort, render_template, render_template_string, flash
from views import force_rest_time

_user_event_id_list = {}

@app.route('/show_event/')
def showEvent():
    header = 'Please carefully read the description of this event'
    if not progress_manager.initialize():
        return redirect(url_for('logout'))
    stepID, question = progress_manager.getNextQuestion()
    if not question:
        flash('No more questions for you.')
        return redirect(url_for('logout'))
    if 'start_time' in session:
        durationInMin = (time.time() - session['start_time']) / 60
        if durationInMin > force_rest_time:
            flash('Please take a break then come back. You have worked for more than %s minutes.' % force_rest_time)
            return redirect(url_for('logout'))

    questionedEventID = question[0]

    ei = EventInfo()
    #ei.eventIDList = ['E%03d' % eventID for eventID in range(21, 41)]   # progress menu
    ei.eventIDList = getEventIDSequence()       # progress bar

    ei.highlightedEventID = questionedEventID
    eventDescriptionFile = r'evid_study/questionnaire/event_info/%s.html' % questionedEventID
    ei.eventDescription = _removeHighlightsFromDescription(open(eventDescriptionFile).read())
    nextPageUrl = url_for('showEventWithHighlight')
    return render_template('event.html', header=header, eventInfo=ei, nextPageUrl=nextPageUrl)


@app.route('/show_event/highlight')
def showEventWithHighlight():
    header = 'Now, read and remember the highlights'
    if not progress_manager.initialize():
        return redirect(url_for('logout'))
    stepID, question = progress_manager.getNextQuestion()
    if not question:
        flash('No more questions for you.')
        return redirect(url_for('logout'))
    questionedEventID = question[0]

    ei = EventInfo()
    #ei.eventIDList = ['E%03d' % eventID for eventID in range(21, 41)]   # progress menu
    ei.eventIDList = getEventIDSequence()       # progress bar

    ei.highlightedEventID = questionedEventID
    eventDescriptionFile = r'evid_study/questionnaire/event_info/%s.html' % questionedEventID
    ei.eventDescription = open(eventDescriptionFile).read()
    nextPageUrl = url_for('showGeneralTips')
    return render_template('event.html', header=header, eventInfo=ei, nextPageUrl=nextPageUrl)


@app.route('/show_event/show_general_tips')
def showGeneralTips():
    if not progress_manager.initialize():
        return redirect(url_for('logout'))
    stepID, question = progress_manager.getNextQuestion()
    if not question:
        flash('No more questions for you.')
        return redirect(url_for('logout'))
    questionedEventID = question[0]
    ei = EventInfo()
    #ei.eventIDList = ['E%03d' % eventID for eventID in range(21, 41)]   # progress menu
    ei.eventIDList = getEventIDSequence()       # progress bar
    ei.highlightedEventID = questionedEventID
    nextPageUrl = url_for('showEventTips')
    return render_template('general_tips.html', eventInfo=ei, nextPageUrl=nextPageUrl)


@app.route('/show_event/show_event_tips')
def showEventTips():
    header = 'To calibrate your judgement, look at a few sample cases'
    if not progress_manager.initialize():
        return redirect(url_for('logout'))
    stepID, question = progress_manager.getNextQuestion()
    if not question:
        flash('No more questions for you.')
        return redirect(url_for('logout'))
    questionedEventID = question[0]
    ei = EventInfo()
    #ei.eventIDList = ['E%03d' % eventID for eventID in range(21, 41)]   # progress menu
    ei.eventIDList = getEventIDSequence()       # progress bar
    ei.highlightedEventID = questionedEventID
    eventTipsFile = r'evid_study/questionnaire/event_tips/%s.html' % questionedEventID
    ei.eventTips = open(eventTipsFile).read()
    return render_template('event_tips.html', header=header, eventInfo=ei)


def getEventIDSequence():
    if session['username'] in _user_event_id_list:
        return _user_event_id_list[session['username']]

    _user_event_id_list[session['username']] = []
    lastEventID = None
    with open(progress_manager.user_data[session['username']]['question_file']) as fin:
        for line in fin:
            splitLine = line.rstrip().split('\t')
            if splitLine[1][0] == 'E' and splitLine[1] != lastEventID:
                lastEventID = splitLine[1]
                _user_event_id_list[session['username']].append(lastEventID)
    return _user_event_id_list[session['username']]


def _removeHighlightsFromDescription(text):
    text = text.replace('<b><font color="brown">', '').replace('</font></b>', '')
    return text


class EventInfo:
    def __init__(self):
        self.eventIDList = None
        self.highlightedEventID = None
        self.eventTitle = None
        self.eventDescription = None
        self.eventTips = None
