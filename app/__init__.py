# Import a module / component using its blueprint handler variable (mod_facerecognition)
from app.mod_facerecognition.controllers import mod_facerecognition as facerecognition_module




# from facial.model import User
# FaceRecognition/README.md at master | habrman/FaceRecognition | GitHub

# CREATE USER 'facerecogn_app'@'localhost' IDENTIFIED BY 'r3c0gn1z3u5pl3@s3';

from app.extensions import db

# Flask files: BEGIN
from flask import Flask, render_template
# import pickle

# Flask(__name__) showed a syntax error, had to do this to get it to work
flaskName = __name__


def register_extensions(app):
    db.init_app(app)


def register_blueprints(app):
    # Register blueprint(s)
    app.register_blueprint(facerecognition_module)
    # app.register_blueprint(xyz_module)
    # ..


def create_app(config):
    app = Flask(flaskName)
    app.config.from_object(config)
    app.config.from_object(__name__)
    # Configurations
    app.config.from_object(config)
    app.config.update(dict(
        JSONIFY_PRETTYPRINT_REGULAR=False
    ))
    app.config.from_envvar('FLASK_SERVER_SETTINGS', silent=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        "mysql+pymysql://facerecogn_app:r3c0gn1z3u5pl3%40s3@localhost:3508/FACERECOGNITION?charset=utf8"
    # app.config['MYSQL_DATABASE_PORT'] = 3508
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    register_extensions(app)
    register_blueprints(app)

    return app


app = create_app('config')


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0')