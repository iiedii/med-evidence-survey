import evid_study
from flask_twisted import Twisted

twisted = Twisted(evid_study.app)
evid_study.app.run(debug=True)
