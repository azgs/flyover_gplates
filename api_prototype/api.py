'''
Flyover Gplates prototype
2019
Stephen Nolan
Arizona Geological Survey

'''

# TODO all "TODO's" need to be cleared before any deployment





# TODO refactor this out if we ever deploy - set ENV, etc
import sys
sys.path.insert(1, '/usr/lib/pygplates/revision18')
import pygplates

import geojson

import flask
from flask import request

app = flask.Flask(__name__)

# TODO - has to be disabled on deploy
app.config["DEBUG"] = True
# app.config["DEBUG"] = False


# Start the actual application
# TODO comment on RCE, only listen if debug is off
# app.run()
# app.run(host='0.0.0.0')







# Root landing page ############################################################
# TODO put some nice simple documentation here specifying API url, params, etc
@app.route('/', methods=['GET'])
def home():
    return "<h1>pygplates flask API prototype</h1><p>work in progress Steve Nolan.</p>"

# Single point rotation ########################################################
@app.route('/single-point', methods=['GET'])
def single_point():

    # TODO agreed on default params (or not, and fail on inalid params)
    # TODO type safety checking - float/string/other
    reconstuct_time = request.args.get('time', 0)
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    roration_model = request.args.get('rotation-model', 'scotese')
    
    point = pygplates.PointOnSphere( (float(latitude), float(longitude)) )

    # data files
    plate_geometry_f = '/home/steve/flyover_gplates/api_prototype/data_sources/scotese_simplified75_epoch.geojson'
    rotation_f = '/home/steve/flyover_gplates/api_prototype/data_sources/scotese.rot'
    rotation_model = pygplates.RotationModel(rotation_f)
    rotation_model = pygplates.RotationModel([rotation_f,plate_geometry_f])

    reconstructed_point = []

    # NOTE what is the hard-coded 0 here?
    # NOTE this function must mutate the reconstructed_motion_paths list,
    # because it is iterated over below, consider tracing this whole function
    # live in an interpreter
    pygplates.reconstruct(point, rotation_model, reconstructed_point,
            reconstuct_time)
            #reconstruct_type=pygplates.ReconstructType.motion_path)


    return latitude + ',' + longitude + ',' + roration_model



# Motion Path ##################################################################
# @app.route('/api/prototype/motion-path', methods=['GET'])
def motion_path():


    # grab all args (using gary's test call as example)
    #https://gws.gplates.org/reconstruct/motion_path/?time=0&seedpoints=75,25,85,25,76,26,85,25&timespec=0,200,2&fixplate=0&movplate=101
    time = request.args.get('time')
    seedpoints = request.args.get('seedpoints')
    timespec = request.args.get('timespec')
    fixplate = request.args.get('fixplate')
    movplate = request.args.get('movplate')


    captured_params = ''

    # args without type (they are all <type 'unicode'>)
    captured_params += 'time: ' + time + ' \n' 
    captured_params += 'seedpoints: ' + seedpoints + '\n'
    captured_params += 'timespec: ' + timespec + '\n'
    captured_params += 'fixplate: ' + fixplate + '\n'
    captured_params += 'movplate: ' + movplate + '\n'

    # print args with type as well
    # captured_params += 'time: ' + time + ' \n' + str(type(time)) + '\n'
    # captured_params += 'seedpoints: ' + seedpoints + ' \n'+ str(type(seedpoints)) + '\n'
    # captured_params += 'timespec: ' + timespec + ' \n'+ str(type(timespec)) + '\n'
    # captured_params += 'fixplate: ' + fixplate + ' \n'+ str(type(fixplate)) + '\n'
    # captured_params += 'movplate: ' + movplate + ' \n'+ str(type(movplate)) + '\n'

    ## entire dict
    # captured_params += repr(request.args)

    captured_params += '\nint time: ' + str(int(time))

    list_of_seedpoints = seedpoints.split(',')
    int_list_of_seedpoints = tuple(int(point) for point in list_of_seedpoints)
    captured_params += '\nint tuple of seedpoints: ' + str(int_list_of_seedpoints)

    timespec_params = timespec.split(',')
    int_list_of_timespec_params = tuple(int(param) for param in timespec_params)
    captured_params += '\nint tuple of timespec: ' + str(int_list_of_timespec_params)

    captured_params += '\nint fixplate: ' + str(int(fixplate))

    captured_params += '\nint movplate: ' + str(int(movplate))


    return captured_params

'''
 STEVE NOTES - talked to gary about the mismatch between function calls here
 and the API example at the gplates api.... 
- time params are passed into their api as one thing, see the 3 ints
- seedpoints need to be pairwise, looks like they get converted to tuples
- fixplate = anchorplate
- movplate = reconstruction_plate_id
- the "time" parameter in the URL string looks to be start time - verify that in
  their graphical application

'''
# Motion Path Transition #######################################################
# @app.route('/api/prototype/motion-path-transition', methods=['GET'])
def transition_route():

    # Specify two (lat/lon) seed points on the present-day African coastline.
    # NOTE list of 2-tules
    seed_points = pygplates.MultiPointOnSphere(
            [
                (46.8, -76.6),
                (45.8, -79.6)
                ])


    # NOTE ints
    time_increment = 5
    start_time = 0
    reconstruction_time = 540
    anchor_plate_id = 0 # 'fixplate'
    reconstruction_plate_id = 101

    # Generate a list of times to sample the motion path - from 0 to 90Ma in increment intervals.
    # NOTE range (change to xrange?)
    times = range(start_time, reconstruction_time, time_increment)

    # Create a motion path feature.
    # NOTE 'motion path feature' - note named arguments
    motion_path_feature = pygplates.Feature.create_motion_path(
            seed_points,
            times,
            valid_time=(max(times), min(times)),
            relative_plate = anchor_plate_id,
            reconstruction_plate_id = reconstruction_plate_id)


    # NOTE data files
    plate_geometry_f = '/home/steve/pygplates_flask_prototype/api_prototype/data_sources/scotese_simplified75_epoch.geojson'
    rotation_f = '/home/steve/pygplates_flask_prototype/api_prototype/data_sources/scotese.rot'


    # Load one or more rotation files into a rotation model.
    # NOTE not sure what's happening here, would need to know what RotationModel
    # returns.... are they overwriting rotation_model? or does that function
    # return some appended thing of what's passed in?
    # TODO check this for correct behavior
    rotation_model = pygplates.RotationModel(rotation_f)
    rotation_model = pygplates.RotationModel([rotation_f,plate_geometry_f])

    # Reconstruct the motion path feature to the reconstruction time.
    # NOTE start with empty list - this may be the main data structure, see how
    # it is used below.... if everything is here it might make sense to 'grab'
    # this and move to JSON/ GeoJSON from there....check if this thing is some
    # kind of dict, etc
    reconstructed_motion_paths = []

    # NOTE what is the hard-coded 0 here?
    # NOTE this function must mutate the reconstructed_motion_paths list,
    # because it is iterated over below, consider tracing this whole function
    # live in an interpreter
    pygplates.reconstruct(motion_path_feature, rotation_model, reconstructed_motion_paths, 0,
            reconstruct_type=pygplates.ReconstructType.motion_path)

    # NOTE is this used ?
    timeString = ''


    # steve temp return string
    return_string = ''

     # Iterate over all reconstructed motion paths.
    return_string +=  ' {"type": "FeatureCollection","features": [ '
    for reconstructed_motion_path in reconstructed_motion_paths:
        motion_path_times = reconstructed_motion_path.get_feature().get_times()
        if len(timeString) == 0:
              return_string +=  '{"type": "Feature", "geometry": { "type": "LineString", "coordinates": [ '
        else:
              return_string +=  ',{"type": "Feature", "geometry": { "type": "LineString", "coordinates": [ '
        # Iterate over the points in the motion path.
        timeString = ''
        for point_index, point in enumerate(reconstructed_motion_path.get_motion_path()):
            lat, lon = point.to_lat_lon()
            # The first point in the path is the oldest and the last point is the youngest.
            # So we need to start at the last time and work our way forwards.
            if len(timeString) == 0:
                timeString =  str(int(motion_path_times[point_index]))
                return_string +=  '[%f,%f]' % (lon,lat)
            else:
                timeString =  timeString + ',' + str(int(motion_path_times[point_index]))
                return_string +=  ',[%f,%f] ' % (lon, lat)
        return_string +=  ' ]}, "properties" : { "times": "%s", "plate_id" : "%s" } }'  % (timeString, reconstruction_plate_id) 
        return_string +=  '] }'

    # TODO delete 
    #return "transition"
    return return_string





# Motion Path Transition #######################################################
app.run()
