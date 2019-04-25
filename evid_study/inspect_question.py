'''
For after survey analysis
'''

import os
from random import shuffle
from evid_study import app
from show_event import EventInfo
from show_question import ImageTable, VideoTable
from flask import Flask, request, redirect, url_for, render_template

# Inputs
video_frame_info_dir = r'evid_study/questionnaire/video_frame_info'
evid_frame_info_dir = r'evid_study/questionnaire/evid_frame_info'
evid_cluster_info_dir = r'evid_study/questionnaire/evid_cluster_info'
dataset_info_dir = r'dataset'
# Data
_inspect_data = {}


@app.route('/inspect_question', methods=['GET'])
def inspectQuestion():
    _loadInspectData()

    videoID = request.args.get('videoid')
    questionType = request.args.get('questiontype')
    if videoID not in _inspect_data['video_frame_info'] or questionType not in map(str, range(1, 6)):
        return redirect(url_for('logout'))

    ei = EventInfo()
    ei.eventIDList = []
    ei.eventTitle = '##### Evidence inspection #####'
    if questionType != '5':
        it = _genImageTable(videoID, questionType)
        return render_template('question_img.html', eventInfo=ei, imageTable=it)
    else:
        vt = _genVideoTable(videoID, questionType)
        return render_template('question_vid.html', eventInfo=ei, videoTable=vt)


def _loadInspectData():
    if _inspect_data:
        return

    _inspect_data['video_frame_info'] = {}
    _inspect_data['evid_frame_info'] = {}
    _inspect_data['evid_cluster_info'] = {}

    # Load video frame info
    eventIDList = [fileName.replace('.txt', '') for fileName in os.listdir(video_frame_info_dir) if fileName.endswith('.txt')]
    for eventID in eventIDList:
        frameInfoFile = os.path.join(video_frame_info_dir, '%s.txt' % eventID)
        with open(frameInfoFile) as fin:
            for line in fin:
                splitLine = line.rstrip().split('\t')
                assert len(splitLine) == 3
                startEndFrames = splitLine[2].split(',')
                _inspect_data['video_frame_info'][splitLine[0]] = [splitLine[1], startEndFrames]

    # Load evidential frame info
    for eventID in eventIDList:
        evidFrameInfoFile = os.path.join(evid_frame_info_dir, '%s.txt' % eventID)
        with open(evidFrameInfoFile) as fin:
            for line in fin:
                splitLine = line.rstrip().split('\t')
                assert len(splitLine) == 3
                evidFrameList = splitLine[2].split(',')
                _inspect_data['evid_frame_info'][splitLine[0]] = [splitLine[1], evidFrameList]

    # Load evidential cluster info
    for eventID in eventIDList:
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
                _inspect_data['evid_cluster_info'][splitLine[0]] = [splitLine[1], clusteredFrameList]



def _genVideoTable(videoID, questionType):
    '''
    Question type:
        - 5: 3 evidential snippets (extended from Type 3 in _genImageTable)
    Return:
        An instance of VideoTable
    '''
    assert questionType == '5'
    vt = VideoTable()
    evidFrameNumbers = _inspect_data['evid_frame_info'][videoID][1]
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
            imgFilePath = os.path.join(dataset_info_dir, _inspect_data['video_frame_info'][videoID][0], '%s_%s_RKF.jpg' % (videoID, frameNumbers[i])).replace('\\', '/')
            it.imageMat[i][0] = url_for('static', filename=imgFilePath)
        return it
    elif questionType == '3':
        evidFrameNumbers = _inspect_data['evid_frame_info'][videoID][1]
        assert len(evidFrameNumbers) <= 3
        it.maxWidth = 1
        it.maxHeight = len(evidFrameNumbers)
        it.imageMat = [['' for i in range(it.maxWidth)] for i in range(it.maxHeight)]
        for i in range(it.maxHeight):
            imgFilePath = os.path.join(dataset_info_dir, _inspect_data['evid_frame_info'][videoID][0], '%s_%s_RKF.jpg' % (videoID, evidFrameNumbers[i])).replace('\\', '/')
            it.imageMat[i][0] = url_for('static', filename=imgFilePath)
        return it
    elif questionType == '4':
        evidClusters = _inspect_data['evid_cluster_info'][videoID][1]
        assert len(evidClusters) <= 3
        maxClusterSize = _getMaxClusterSize(evidClusters)
        it.maxWidth = 3 if maxClusterSize >= 3 else maxClusterSize
        it.maxHeight = len(evidClusters)
        it.imageMat = [['' for i in range(it.maxWidth)] for i in range(it.maxHeight)]
        for i in range(it.maxHeight):
            for j in range(it.maxWidth):
                if j < len(evidClusters[i]):
                    imgFilePath = os.path.join(dataset_info_dir, _inspect_data['evid_cluster_info'][videoID][0], '%s_%s_RKF.jpg' % (videoID, evidClusters[i][j])).replace('\\', '/')
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
    start = int(_inspect_data['video_frame_info'][videoID][1][0])
    end = int(_inspect_data['video_frame_info'][videoID][1][1])
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

