# Import flask dependencies
from flask import Blueprint, request, jsonify

from sklearn.metrics.pairwise import pairwise_distances
from scipy import misc
import tensorflow as tf
import app.mod_face_utils.detect_and_align as detect_and_align
import os
import base64
import requests
import json
from json_tricks import dumps
import random
import string

from app.extensions import db

# Import module models (i.e. User)
from app.mod_facerecognition.models import User, Article

# Define the blueprint: 'facerecognition', set its url prefix: app.url/auth
mod_facerecognition = Blueprint('facerecognition', __name__, url_prefix='/facerecognition')


DISTANCE_THRESHOLD = 1.0
SERVER_URL = "http://178.128.35.109:8501/v1/models/facerecognition_model:predict"


@mod_facerecognition.route('/save_user/', methods=['POST'])
def save_user():
    # global mtcnn
    response_message = 'Default error message'
    response_status = False

    # grabbing a set of features from the request's body
    image_base64 = request.get_json()['image']
    username = request.get_json()['username']
    password = request.get_json()['password']
    name = request.get_json()['name']

    output_vector_128 = get_image_as_128vector(image_base64)

    if type(output_vector_128) is str:
        try:
            user = User(username=username, password=password, name=name, embeddings=output_vector_128)
            db.session.add(user)
            db.session.commit()
            response_message = "Successfully saved new user!"
            response_status = True
        except:
            response_message = "Could not save user, try another username!"
    else:
        response_message = "An error occurred while trying to get face embeddings from AI model!"

    data = {"success": response_status, "message": response_message}

    return jsonify(data)


@mod_facerecognition.route('/users/')
def get_users():
    users = User.query.all()
    return dumps([user.to_dict() for user in users])


@mod_facerecognition.route('/save_article/', methods=['POST'])
def save_articles():
    # global mtcnn
    response_message = 'Default error message'
    response_status = False

    # grabbing a set of features from the request's body
    link = request.get_json()['link']
    image = request.get_json()['image']
    name = request.get_json()['name']
    summary = request.get_json()['summary']

    article = Article.query.filter_by(name=name).first()

    try:
        if article is not None:
            article.link = link
            article.image = image
            article.summary = summary
            db.session.commit()
            response_message = "Successfully updated article details!"
        else:
            article = Article(name=name, link=link, summary=summary)
            db.session.add(article)
            db.session.commit()
            response_message = "Successfully saved new article!"
        response_status = True
    except:
        response_message = "Could not save article, maybe try another name!"

    data = {"success": response_status, "message": response_message}

    return jsonify(data)


@mod_facerecognition.route('/articles/')
def get_articles():
    articles = Article.query.all()
    return dumps([article.to_dict() for article in articles])


# Set the route and accepted methods
@mod_facerecognition.route('/authenticate_user/', methods=['POST'])
def authentication():

    status = False
    response_message = "Unknown authentication request! " \
                       "Use either username and password OR username and face."

    request_json = request.get_json()

    if 'image' in request_json and 'username' in request_json:
        data = auth_by_face(request_json)
    elif 'password' in request_json and 'username' in request_json:
        data = auth_by_password(request_json)
    else:
        data = {"success": status, "message": response_message, "user": None}

    return jsonify(data)


def auth_by_password(request_json):
    status = False
    user_data = None
    response_message = "Incorrect username or password!"

    # grabbing a username and password from the request's body
    password = request_json['password']
    username = request_json['username']
    user = User.query.filter_by(username=username).first()

    if user is not None and user.check_password(password):
        status = True
        user_data = {"name": user.name}
        response_message = "Successfully authenticated user!"

    data = {"success": status, "message": response_message, "user": user_data}

    return data


def auth_by_face(request_json):
    status = False
    user_data = None
    response_message = "Failed to recognize that face! Try again in different angle, lighting, and/or camera distance."

    # grabbing a set of features from the request's body
    image_base64 = request_json['image']
    username = request_json['username']

    user = User.query.filter_by(username=username).first()

    if user is not None:

        vector_128 = get_image_as_128vector(image_base64)

        if type(vector_128) is str:
            vector_128 = json.loads(vector_128)
            user_vector_128 = json.loads(user.embeddings)
            distance_matrix = pairwise_distances([user_vector_128], [vector_128])

            if distance_matrix[0][0] < DISTANCE_THRESHOLD:
                status = True
                user_data = {"name": user.name}
                response_message = "Successfully authenticated your face!"

    else:
        response_message = "Username does not exist!"

    data = {"success": status, "message": response_message, "user": user_data}

    return data


def get_random_string():
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])


def convert_and_save(b64_string, image_path='upload_image.png'):
    b64_string = b64_string.partition(',')[2]
    pad = len(b64_string) % 4
    b64_string += "="*pad
    with open(image_path, "wb") as fh:
        fh.write(base64.decodebytes(b64_string.encode()))


def get_image_as_128vector(image_base64):
    temp_image_name = get_random_string() + '.png'
    image_path = '/var/www/facerecognition/FaceRecognitionBackend/.temp_images/' + temp_image_name

    convert_and_save(image_base64, image_path)

    tf.reset_default_graph()

    with tf.Session() as sess:
        # Setup models
        mtcnn = detect_and_align.create_mtcnn(sess, None)

        # Locate faces and landmarks in frame
        image = misc.imread(os.path.expanduser(image_path), mode='RGB')
        face_patches, padded_bounding_boxes, landmarks = detect_and_align.detect_faces(image, mtcnn)

    face_patches = dumps(face_patches, primitives=True)
    face_patches = json.loads(face_patches)
    feed_dict = {'inputs': {'input': face_patches, 'phase_train': False}}

    response = requests.post(SERVER_URL, json=feed_dict)  # , headers=headers)

    if response.status_code == 200:
        outputs = response.json()
        output_vector_128 = dumps(outputs['outputs'][0])  # convert to string
    else:
        output_vector_128 = None

    if os.path.exists(image_path):  # delete temporary file after use
        os.remove(image_path)

    return output_vector_128

