import os
from random import shuffle
from evid_study import app, progress_manager
from show_event import EventInfo
from show_event import getEventIDSequence
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash


# Inputs
video_frame_info_dir = r'evid_study/questionnaire/video_frame_info'
evid_frame_info_dir = r'evid_study/questionnaire/evid_frame_info'
evid_cluster_info_dir = r'evid_study/questionnaire/evid_cluster_info'
dataset_info_dir = r'dataset'
# Data
_questionnaire_data = {}


@app.route('/show_question/')
def showQuestion():
    if not progress_manager.initialize():
        return redirect(url_for('logout'))

    _init(session['username'])

    if request.referrer and 'show_event' in request.referrer:            # just came in
        stepID, question = progress_manager.getNextQuestion(isSaveAction=True)
    else:
        stepID, question = progress_manager.getNextQuestion()
    if _isGameOver(stepID):
        flash("You have finished all questions. Thank you for your contribution.")
        return redirect(url_for('logout'))

    if len(question) == 1:      # an event tag
        if request.referrer and 'show_event' in request.referrer:        # just showed
            stepID, question = progress_manager.moveToNextQuestion()
        else:
            return redirect(url_for('showEvent'))
    if _isGameOver(stepID):
        flash("You have finished all questions. Thank you for your contribution.")
        return redirect(url_for('logout'))
    
    assert len(question) == 3
    questionedEventID = question[0]
    questionedVideoID = question[1]
    questionType = question[2]

    if (_questionnaire_data[session['username']]['_loaded_event_id'] != questionedEventID):
        _loadDataInfo(questionedEventID)

    ei = EventInfo()
    #ei.eventIDList = ['E%03d' % eventID for eventID in range(21, 41)]   # progress menu
    ei.eventIDList = getEventIDSequence()       # progress bar
    ei.highlightedEventID = questionedEventID
    eventTitleFile = r'evid_study/questionnaire/event_title/%s.txt' % questionedEventID
    ei.eventTitle = open(eventTitleFile).read()

    if questionType != '5':
        it = _genImageTable(questionedVideoID, questionType)
        session['step_id'] = stepID
        return render_template('question_img.html', eventInfo=ei, imageTable=it)
    else:
        vt = _genVideoTable(questionedVideoID, questionType)
        session['step_id'] = stepID
        return render_template('question_vid.html', eventInfo=ei, videoTable=vt)



@app.route('/show_question/post_answer', methods=['POST'])
def postAnswer():
    if not progress_manager.initialize():
        return redirect(url_for('logout'))
    
    if request.method == "POST":
        if 'answer' not in request.form:
            return redirect(url_for('showQuestion'))
        if not progress_manager.writeUserAnswer(request.form['answer'], session['step_id'], request.form['loadingtime']):
            return redirect(url_for('showQuestion'))

        progress_manager.moveToNextQuestion()
        return redirect(url_for('showQuestion'))
    return redirect(url_for('logout'))


def _isGameOver(stepID):
    if stepID == 'ID0FFF':      # game over
        return True
    return False


def _genVideoTable(videoID, questionType):
    '''
    Question type:
        - 5: 3 evidential snippets (extended from Type 3 in _genImageTable)
    Return:
        An instance of VideoTable
    '''
    assert questionType == '5'
    vt = VideoTable()
    evidFrameNumbers = _questionnaire_data[session['username']]['_evid_frame_info'][videoID][1]
    assert len(evidFrameNumbers) <= 3
    vt.maxWidth = 1
    vt.maxHeight = len(evidFrameNumbers)
    vt.videoMat = [['' for i in range(vt.maxWidth)] for i in range(vt.maxHeight)]
    for i in range(vt.maxHeight):
        vidFilePath = os.path.join(dataset_info_dir, 'evid_snippets', '%s_s%s.mp4' % (videoID, evidFrameNumbers[i])).replace('\\', '/')
        vt.videoMat[i][0] = url_for('static', filename=vidFilePath)
    return vt


def _genImageTable(videoID, questionType):
    '''
    Question type:
        - 1: 3 random frames
        - 2: Start-mid-end frames
        - 3: 3 evidential frames
        - 4: 3 evidential clusters
    Return:
        An instance of ImageTable
    '''
    it = ImageTable()
    if questionType == '1' or questionType == '2':
        isRandom = True if questionType == '1' else False
        frameNumbers = _getFixedFrames(videoID, isRandom)
        it.maxWidth = 1
        it.maxHeight = len(frameNumbers)
        it.imageMat = [['' for i in range(it.maxWidth)] for i in range(it.maxHeight)]
        for i in range(it.maxHeight):
            imgFilePath = os.path.join(dataset_info_dir, _questionnaire_data[session['username']]['_video_frame_info'][videoID][0], '%s_%s_RKF.jpg' % (videoID, frameNumbers[i])).replace('\\', '/')
            it.imageMat[i][0] = url_for('static', filename=imgFilePath)
        return it
    elif questionType == '3':
        evidFrameNumbers = _questionnaire_data[session['username']]['_evid_frame_info'][videoID][1]
        assert len(evidFrameNumbers) <= 3
        it.maxWidth = 1
        it.maxHeight = len(evidFrameNumbers)
        it.imageMat = [['' for i in range(it.maxWidth)] for i in range(it.maxHeight)]
        for i in range(it.maxHeight):
            imgFilePath = os.path.join(dataset_info_dir, _questionnaire_data[session['username']]['_evid_frame_info'][videoID][0], '%s_%s_RKF.jpg' % (videoID, evidFrameNumbers[i])).replace('\\', '/')
            it.imageMat[i][0] = url_for('static', filename=imgFilePath)
        return it
    elif questionType == '4':
        evidClusters = _questionnaire_data[session['username']]['_evid_cluster_info'][videoID][1]
        assert len(evidClusters) <= 3
        maxClusterSize = _getMaxClusterSize(evidClusters)
        it.maxWidth = 3 if maxClusterSize >= 3 else maxClusterSize
        it.maxHeight = len(evidClusters)
        it.imageMat = [['' for i in range(it.maxWidth)] for i in range(it.maxHeight)]
        for i in range(it.maxHeight):
            for j in range(it.maxWidth):
                if j < len(evidClusters[i]):
                    imgFilePath = os.path.join(dataset_info_dir, _questionnaire_data[session['username']]['_evid_cluster_info'][videoID][0], '%s_%s_RKF.jpg' % (videoID, evidClusters[i][j])).replace('\\', '/')
                    it.imageMat[i][j] = url_for('static', filename=imgFilePath)
        return it
    assert questionType != '5'


def _getMaxClusterSize(evidClusters):
    maxClusterSize = 0
    for cluster in evidClusters:
        if len(cluster) > maxClusterSize:
            maxClusterSize = len(cluster)
    return maxClusterSize


def _getFixedFrames(videoID, isRandom=False):
    start = int(_questionnaire_data[session['username']]['_video_frame_info'][videoID][1][0])
    end = int(_questionnaire_data[session['username']]['_video_frame_info'][videoID][1][1])
    assert start == 1
    if end < 2:
        return [1]
    elif end < 3:
        return [1, 2]

    if not isRandom:
        mid = int(start + (end - start) / 2)
        return [start, mid, end]
    else:
        numbers = range(start, end + 1)
        shuffle(numbers)
        return numbers[0:3]         #! it is better to save the result in the activity log (!unfinished)


def _loadDataInfo(eventID):
    _questionnaire_data[session['username']]['_video_frame_info'] = {}
    _questionnaire_data[session['username']]['_evid_frame_info'] = {}
    _questionnaire_data[session['username']]['_evid_cluster_info'] = {}

    # Load video frame info
    frameInfoFile = os.path.join(video_frame_info_dir, '%s.txt' % eventID)
    with open(frameInfoFile) as fin:
        for line in fin:
            splitLine = line.rstrip().split('\t')
            assert len(splitLine) == 3
            startEndFrames = splitLine[2].split(',')
            _questionnaire_data[session['username']]['_video_frame_info'][splitLine[0]] = [splitLine[1], startEndFrames]
    
    # Load evidential frame info
    evidFrameInfoFile = os.path.join(evid_frame_info_dir, '%s.txt' % eventID)
    with open(evidFrameInfoFile) as fin:
        for line in fin:
            splitLine = line.rstrip().split('\t')
            assert len(splitLine) == 3
            evidFrameList = splitLine[2].split(',')
            _questionnaire_data[session['username']]['_evid_frame_info'][splitLine[0]] = [splitLine[1], evidFrameList]

    # Load evidential cluster info
    evidClusterInfoFile = os.path.join(evid_cluster_info_dir, '%s.txt' % eventID)
    with open(evidClusterInfoFile) as fin:
        for line in fin:
            splitLine = line.rstrip().split('\t')
            assert len(splitLine) == 3
            clusteredFrameList = []
            frameStrList = splitLine[2].split(';')
            for frameStr in frameStrList:
                frameList = frameStr.split(',')
                clusteredFrameList.append(frameList)
            _questionnaire_data[session['username']]['_evid_cluster_info'][splitLine[0]] = [splitLine[1], clusteredFrameList]

    _questionnaire_data[session['username']]['_loaded_event_id'] = eventID


def _init(username):
    if username not in _questionnaire_data:
        _questionnaire_data[username] = {}
        _questionnaire_data[username]['_loaded_event_id'] = None



class ImageTable:
    def __init__(self):
        self.maxWidth = None
        self.maxHeight = None
        self.imageMat = None        # this must match the dimension of maxWidth and maxHeight

class VideoTable:
    def __init__(self):
        self.maxWidth = None
        self.maxHeight = None
        self.videoMat = None        # this must match the dimension of maxWidth and maxHeight
