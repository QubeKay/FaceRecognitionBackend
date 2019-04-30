

from flask_sqlalchemy import SQLAlchemy

# from facial.model import User
# FaceRecognition/README.md at master · habrman/FaceRecognition · GitHub

# CREATE USER 'facerecogn_app'@'localhost' IDENTIFIED BY 'r3c0gn1z3u5pl3@s3';


# Flask files: BEGIN
from flask import Flask
# import pickle
from flask import request, render_template, jsonify
# Import a module / component using its blueprint handler variable (mod_facerecognition)
from app.mod_facerecognition.controllers import mod_facerecognition as facerecognition_module


application = Flask(__name__)
application.config.from_object(__name__)
# Configurations
application.config.from_object('config')
application.config.update(dict(
    JSONIFY_PRETTYPRINT_REGULAR=False
))
application.config.from_envvar('FLASK_SERVER_SETTINGS', silent=True)
application.config['SQLALCHEMY_DATABASE_URI'] = \
    "mysql+pymysql://facerecogn_app:r3c0gn1z3u5pl3%40s3@localhost:3508/FACERECOGNITION?charset=utf8"
# application.config['MYSQL_DATABASE_PORT'] = 3508
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(application)


@application.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


# Register blueprint(s)
application.register_blueprint(facerecognition_module)
# app.register_blueprint(xyz_module)
# ..

if __name__ == '__main__':
    application.run(host='0.0.0.0')