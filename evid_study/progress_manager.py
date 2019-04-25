'''
This module manages user progress by file I/O.
'''

import os
from datetime import datetime
from flask import session

# Inputs
current_progress_log_file = r'evid_study/log/$username$/current.log'
user_activity_log_file = r'evid_study/log/$username$/user_activity.log'
question_file = r'evid_study/questionnaire/user_data/$username$/questionnaire.txt'
# Global
user_data = {}


def getNextQuestion(isSaveAction=False):
    currentStepID = None
    if os.path.exists(user_data[session['username']]['current_progress_log_file']):
        with open(user_data[session['username']]['current_progress_log_file']) as fin:
            currentStepID = fin.readline().rstrip()
    if not currentStepID:
        currentStepID = user_data[session['username']]['_question_table']['__first_id__']

    if currentStepID in user_data[session['username']]['_question_table']:
        question = user_data[session['username']]['_question_table'][currentStepID]
    else:
        currentStepID = 'ID0FFF'    # game over
        question = None

    if isSaveAction:
        _saveAction('%s\t%s\t%s\t%s' % (datetime.now(), 'GET_CURR', currentStepID, 'User opened this question.'))
    return currentStepID, question


def moveToNextQuestion():
    currentStepID = None
    if os.path.exists(user_data[session['username']]['current_progress_log_file']):
        with open(user_data[session['username']]['current_progress_log_file']) as fin:
            currentStepID = fin.readline().rstrip()
    if not currentStepID:
        currentStepID = user_data[session['username']]['_question_table']['__first_id__']

    currentStepID = _getNextStepID(currentStepID)
    if currentStepID in user_data[session['username']]['_question_table']:
        question = user_data[session['username']]['_question_table'][currentStepID]
    else:
        currentStepID = 'ID0FFF'    # game over
        question = None
    
    _saveProgress(currentStepID)
    _saveAction('%s\t%s\t%s\t%s' % (datetime.now(), 'GET_NEXT', currentStepID, 'User moved to this question.'))
    return currentStepID, question


def writeUserAnswer(answer, submittedStepID, loadingTime):
    answer = answer.upper()
    currentStepID = None
    if os.path.exists(user_data[session['username']]['current_progress_log_file']):
        with open(user_data[session['username']]['current_progress_log_file']) as fin:
            currentStepID = fin.readline().rstrip()
    if not currentStepID:
        currentStepID = user_data[session['username']]['_question_table']['__first_id__']

    if currentStepID != submittedStepID:
        return False

    question = user_data[session['username']]['_question_table'][currentStepID]
    questionType = question[2]
    _saveAction('%s\t%s\t%s\tTYPE%s\t%sms\t%s\t%s' % (datetime.now(), 'POS_ANSR', currentStepID, questionType, loadingTime, answer, 'User answered this question.'))
    return True


def writeLogin():
    _saveAction('%s\t%s\t%s\t%s' % (datetime.now(), 'USR_LGIN', session['username'], 'User logged in.'))

def writeLogout():
    _saveAction('%s\t%s\t%s\t%s' % (datetime.now(), 'USR_LGOT', session['username'], 'User logged out.'))


def _saveAction(action):
    with open(user_data[session['username']]['user_activity_log_file'], 'a') as fout:
        fout.write('%s\n' % action)


def _saveProgress(currentStepID):
    with open(user_data[session['username']]['current_progress_log_file'], 'w') as fout:
        fout.write('%s\n' % currentStepID)


def _getNextStepID(stepIDStr):
    stepID = int(stepIDStr[2:])
    stepID += 1
    return 'ID%04d' % stepID


def _loadQuestionTable():
    user_data[session['username']]['question_file'] = question_file.replace('$username$', session['username'])
    user_data[session['username']]['_question_table'] = {}

    with open(user_data[session['username']]['question_file']) as fin:
        lineID = 0
        for line in fin:
            lineID += 1
            splitLine = line.rstrip().split('\t')
            assert len(splitLine) > 1
            stepID = splitLine[0]
            question = splitLine[1:]
            if lineID == 1:
                user_data[session['username']]['_question_table']['__first_id__'] = stepID
            user_data[session['username']]['_question_table'][stepID] = question


def _createLogDir():
    user_data[session['username']]['current_progress_log_file'] = current_progress_log_file.replace('$username$', session['username']).replace('\\', '/')
    user_data[session['username']]['user_activity_log_file'] = user_activity_log_file.replace('$username$', session['username']).replace('\\', '/')
    current_progress_log_dir = user_data[session['username']]['current_progress_log_file'][:user_data[session['username']]['current_progress_log_file'].rfind('/')]
    user_activity_log_dir = user_data[session['username']]['user_activity_log_file'][:user_data[session['username']]['user_activity_log_file'].rfind('/')]
    if not os.path.exists(current_progress_log_dir): os.mkdir(current_progress_log_dir)
    if not os.path.exists(user_activity_log_dir): os.mkdir(user_activity_log_dir)


def initialize():
    global _question_username
    if 'username' not in session:
        return False

    if session['username'] not in user_data:
        user_data[session['username']] = {}
        _loadQuestionTable()
        _createLogDir()
    return True
