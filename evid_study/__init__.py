from flask import Flask

userBook = dict(line.rstrip().split('\t') for line in open('evid_study/questionnaire/users.txt').readlines())

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    SECRET_KEY='\xbcw\x8d\xbb\xc2\xb3n1LKM\xcd-\xe9C\x95\x98\xcf3\xe0eA\x7f\x11\x8dDp\xd63\x1f\xd7|',
    USERBOOK=userBook
))
app.config.from_envvar('EVID_STUDY_SETTINGS', silent=True)          # optional

import evid_study.views
