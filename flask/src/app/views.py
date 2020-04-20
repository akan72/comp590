# from flask import request, render_template, flash, redirect, url_for, session, send_from_directory
# import os
# import json
# from typing import List
# from PIL import Image

# import src.models.iris_model as iris_model
# import src.models.planet_model as planet_model

# from src.app import app

# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# # Index
# @app.route('/')
# def home():
#     return render_template('index.html')

# ### PREDICTIONS 

# # Predict petal length within the application
# @app.route('/predict', methods=['GET', 'POST'])
# def predict_petal_length():
#     petal_width = request.args.get('petal_width')

#     prediction_results = iris_model.predict_length(petal_width)
#     response = json.dumps(prediction_results[0])

#     return response

# # Predict petal length with a POST request to /predict_api
# @app.route('/predict_petal_length_api', methods=['GET', 'POST'])
# def predict_petal_length_api():
#     data = request.get_json()
#     petal_width = data['petal_width']

#     prediction_results = iris_model.predict_length(petal_width)
#     response = json.dumps(prediction_results[0])

#     return response

# ### FILE UPLOADS

# # Function to determine if the filename is valid and the image if a valid type
# def allowed_file(filename: str):
#     """ Determine if filename is valid.

#     Function that determines if an image is valid upload to
#     the Flask application given its extension {.png, .jpg, .jpeg}.

#     Arguments:
#         filename [str]: Path to the filename relative to the extension. 
    
#     Returns:
#         boolean: True if file extension is valid else false.

#     """
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# # Upload the file to our system
# @app.route('/upload', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         files = request.files.getlist('file')

#         filenames = []
#         results = []
#         for file in files:
#             name = file.filename
#             if allowed_file(name):
#                 filenames.append(name)

#                 filepath = os.path.join(app.config['UPLOAD_FOLDER'], name)
#                 file.save(filepath)

#                 prediction_results = planet_model.predict_landcover_type(filepath)
#                 results.append(prediction_results)
        
#         content = dict(zip(filenames, results))
        
#         return render_template('planet.html', content=content)

#     return render_template('file_upload.html')

# @app.route('/upload_file_api', methods=['POST'])
# def upload_file_api():
#     filenames, results = [], []

#     for file in request.files.keys():
#         file = request.files[file]
#         name = file.filename
#         if allowed_file(name):
#             filenames.append(name)

#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], name)
#             file.save(filepath)

#             prediction_results = planet_model.predict_landcover_type(filepath)
#             results.append(prediction_results)
    
#     content = dict(zip(filenames, results))

#     return content

# # Endpoint to serve back the uploaded image within planet.html
# @app.route('/data/uploads/<filepath>')
# def serve_file(filepath):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename=filepath)

# ### MISC 
# @app.route('/dashboard', methods=['GET'])
# def do_plot():
#     return render_template('dashboard.html')

import os, sys
import json
import random
import pickle
import datetime
from flask import request, render_template, url_for, send_from_directory, jsonify, Blueprint

from src.app import app, db
from src.app.models import PlanetPrediction
import src.models.iris_model as iris_model
import src.models.planet_model as planet_model

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Index
@main.route('/')
def index():
    return render_template('index.html')

### PREDICTIONS 
@main.route('/iris')
def iris():
    return render_template('iris.html')

# Predict petal length with a POST request or within the application form
# TODO: Multiple uploads
@main.route('/predict_petal_length_api', methods=['GET', 'POST'])
@main.route('/predict_petal_length', methods=['GET', 'POST'])
def predict_petal_length():
    # Allow for handling of form input, well as field and JSON input
    if request.is_json:
        petal_width = request.get_json()['petal_width']
    else: 
        petal_width = request.values['petal_width']

    prediction_results = iris_model.predict_length(petal_width)
    response = json.dumps(prediction_results[0])

    # If the request path is from the GUI, then render the correct template, return a JSON of model results
    if request.path == '/predict_petal_length':
        content = dict(zip(petal_width, response))

        return render_template('iris_result.html', content=content)

    return jsonify(response)

### FILE UPLOADS

# Function to determine if the filename is valid and the image if a valid type
def allowed_file(filename: str):
    """Determine if filename is valid.

    Function that determines if an image is valid upload to
    the Flask application given its extension {.png, .jpg, .jpeg}.

    Arguments:
        filename [str]: Path to the filename relative to the extension. 
    
    Returns:
        boolean: True if file extension is valid else false.

    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload the file to our system
@main.route('/upload_image_api', methods=['GET', 'POST'])
@main.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    # If the API does not receive a POST request, return back to the image upload page
    if request.method == 'POST':
        images, filenames = [], []

        # If the image input is in JSON format, iterate over the keys and save files with valid extensions
        if request.is_json: 
            for file in request.files.keys():
                image = request.files[file]
                name = file.filename

                if allowed_file(name):
                    images.append(image)
                    filenames.append(name)

        # If image input is thorugh a form, do the same 
        else:
            for file in request.files.getlist('file'):
                name = file.filename

                if allowed_file(name):
                    images.append(file)
                    filenames.append(name)
  
        results = []
        
        # Iterate over all of the valid files and save to the filesystem
        for file, name in zip(images, filenames):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], name)
            file.save(filepath)

            # Run the landcover prediction model on the file and save results
            prediction_results = planet_model.predict_landcover_type(filepath)

            results.append(prediction_results)
        
            new_prediction = PlanetPrediction(
                userID=random.randint(0, 100),
                time=datetime.datetime.now(),
                modelType='Planet Kaggle Amazon',
                image=filepath,
                result=results
            )

            db.session.add(new_prediction)
            db.session.commit()

        # Zip together results with file names for storage
        output = dict(zip(filenames, results))

        # If calling the endpoint through the application, render the results page, else just return the predictions
        if request.path == '/upload_image':
            return render_template('image_result.html', content=output)

        return jsonify(output)

    return render_template('image_upload.html')

# Endpoint to serve back the uploaded image to image_result.html
@main.route('/data/uploads/<filepath>')
def serve_file(filepath):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename=filepath)

@main.route('/test')
def test():
    return jsonify({'k1': 'v1', 'k2': 'v2', 'k3': 'v3'})
