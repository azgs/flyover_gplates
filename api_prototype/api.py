#!/usr/bin/env python

'''
Flyover Gplates prototype
2019
Stephen Nolan
Arizona Geological Survey
'''

# TODO all "TODO's" need to be cleared before any production deployment


# TODO refactor this out if we ever deploy - set ENV, etc
import sys
sys.path.insert(1, '/usr/lib/pygplates/revision18')

import json
import flask
from flask import request, jsonify
import pygplates
from shapely.geometry import Point, Polygon

app = flask.Flask(__name__)


# Root landing page ############################################################
@app.route('/', methods=['GET'])
def home():
    return '<h1>pygplates flask API prototype</h1><p>work in progress Steve Nolan.</p>'


# Single point plate intersection, present day  ################################
@app.route('/single-point-present-day', methods=['GET'])
def single_point_present_day():

    # will return plateID if query point intersects a plate, otherwise no plate found
    return_data = 'no plate found'

    # TODO safetey checks on params, possible forced defaults, throw errors on
    # invalid types

    # Grab params, apply defaults
    longitude = float(request.args.get('longitude'))
    latitude = float(request.args.get('latitude'))
    plate_model = request.args.get('plate-model', 'scotese')
    
    # Query point
    query_point = Point(longitude, latitude)

    # TODO in the future we may make this interchangeable for the various query
    # types, will need to support different models and their associated files

    # Open plate specification file
    with open('./data_sources/scotese_plates.geojson', 'r') as model_file:
        scotese_model = json.load(model_file)


    # TODO validate that this is the correct/safe way to parse the geojson, 
    # specifically, alternatives to hard coded array indexing

    # Iterate over plates, test for intersection
    for feature in scotese_model['features']:

        # grab coordinates set 
        coordinates = feature['geometry']['coordinates'][0]

        # build polygon from them
        polygon = Polygon(coordinates)

        # test for intersection, if found, return plateID
        if(polygon.contains(query_point)):
            intersected_plate = feature['properties']['PlateID']
            return_data = intersected_plate 
            break

    # TODO verify desired formatting of returned JSON
    return jsonify({'plateID' : return_data})


# Run configuration ############################################################

# TODO - has to be FALSE on deploy
app.config['DEBUG'] = True      # for testing ONLY
# app.config['DEBUG'] = False

# TODO - has to be app.run() on deploy
# Start the application
app.run()                       # listen on localhost
# app.run(host='0.0.0.0')       # listen on the local IP - for testing ONLY
