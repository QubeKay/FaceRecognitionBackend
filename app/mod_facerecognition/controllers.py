# Import flask dependencies
from flask import Blueprint

from sklearn.metrics.pairwise import pairwise_distances
from scipy import misc
import tensorflow as tf
import detect_and_align
import os
import base64
import requests
import json
from json_tricks import dumps
import random
import string
from flask import request
from flask import jsonify

# Import the database object from the main app module
from app import db

# Import module forms
# from app.mod_auth.forms import LoginForm

# Import module models (i.e. User)
from app.mod_facerecognition.models import User

# Define the blueprint: 'facerecognition', set its url prefix: app.url/auth
mod_facerecognition = Blueprint('facerecognition', __name__, url_prefix='/facerecognition')


DISTANCE_THRESHOLD = 0.6
SERVER_URL = "http://178.128.35.109:8501/v1/models/facerecognition_model:predict"


@mod_facerecognition.route('/save_user/', methods=['POST'])
def save_user():
    # global mtcnn
    response_message = 'Default error message'

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
        except:
            response_message = "DB Error: Could not save user, try another username!"
    else:
        response_message = "An error occurred while trying to get face embeddings from AI model!"

    return response_message


@mod_facerecognition.route('/users/')
def users():
    users = User.query.all()
    return dumps([user.to_dict() for user in users])

# Set the route and accepted methods
@mod_facerecognition.route('/authenticate_user/', methods=['POST'])
def authentication():

    status = False
    response_message = "Failed to match faces!"

    # grabbing a set of features from the request's body
    image_base64 = request.get_json()['image']
    username = request.get_json()['username']
    user = User.query.filter_by(username=username).first()

    vector_128 = get_image_as_128vector(image_base64)

    if type(vector_128) is str:
        vector_128 = json.loads(vector_128)
        user_vector_128 = json.loads(user.embeddings)
        distance_matrix = pairwise_distances([user_vector_128], [vector_128])

        if distance_matrix[0][0] < DISTANCE_THRESHOLD:
            status = True
            response_message = "Successfully matched faces!"

    data = {"success": status, "message": response_message}

    # data = {}
    # data['success'] = status
    # data['message'] = response_message

    return jsonify(data)


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
    image_path = './.temp_images/' + temp_image_name

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

