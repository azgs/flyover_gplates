# TODO refactor this out if we ever deploy - set ENV, etc
import sys
sys.path.insert(1, '/usr/lib/pygplates/revision18')
import pygplates



import flask
from flask import request

app = flask.Flask(__name__)

# TODO disable if this is ever deployed outside of AZGS GIS
app.config["DEBUG"] = True
# app.config["DEBUG"] = False


# TODO put some nice simple documentation here specifying API url, params, etc
@app.route('/', methods=['GET'])
def home():
    return "<h1>pygplates flask API prototype</h1><p>work in progress Steve Nolan.</p>"


# TODO discuss with gary what naming convention/path we want on this
# This route is intended to be the one we use... test transitional route below
# to port gary's stdout code to this flask route
@app.route('/api/prototype/motion-path', methods=['GET'])
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
  their graphical application, make TODO note to ask gary about this

'''
# TODO get this serving out on GET requests, pushing the right data (GeoJSON or
# not), then work on parameterizing everything. Feel free to just serve the
# string for now, as a test to have this on flask, functions calling OK, etc
# the actual used route will be diferent entity above
@app.route('/api/prototype/motion-path-transition', methods=['GET'])
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


# Start the actual application
# TODO comment on RCE, only listen if debug is off
# app.run()
app.run(host='0.0.0.0')












'''
https://github.com/GPlates/gplates-web-service/blob/master/django/GWS/reconstruct/views.py

django example here from their web service... we won't use their code verbatim,
but we can use THEIR model for conventions as to which defautls we want to set
in the calls. Essentially, using theirs as the reference implementation



'''


def motion_path_reference(request):
    """
    http GET request to retrieve reconstructed static polygons
    **usage**
    
    <http-address-to-gws>/reconstruct/motion_path/seedpoints=\ *points*\&timespec=\ *time_list*\&fixplate=\ *fixed_plate_id*\&movplate=\ *moving_plate_id*\&time=\ *reconstruction_time*\&model=\ *reconstruction_model*
    
    :param seedpoints: integer value for reconstruction anchor plate id [required]
    :param timespec: specification for times for motion path construction, in format 'mintime,maxtime,increment' [defaults to '0,100,10']
    :param time: time for reconstruction [default=0]
    :param fixplate: integer plate id for fixed plate [default=0]
    :param movplate: integer plate id for moving plate [required]
    :param model: name for reconstruction model [defaults to default model from web service settings]
    :returns:  json containing reconstructed motion path features
    """





    seedpoints = request.GET.get('seedpoints', None)
    times = request.GET.get('timespec', '0,100,10')
    reconstruction_time = request.GET.get('time', 0)
    RelativePlate = request.GET.get('fixplate', 0)
    MovingPlate = request.GET.get('movplate', None)
    model = request.GET.get('model',settings.MODEL_DEFAULT)

    points = []
    if seedpoints:
        ps = seedpoints.split(',')
        if len(ps)%2==0:
            for lat,lon in zip(ps[1::2], ps[0::2]):
                points.append((float(lat),float(lon)))

    seed_points_at_digitisation_time = pygplates.MultiPointOnSphere(points)

    if times:
        ts = times.split(',')
        if len(ts)==3:
            times = np.arange(float(ts[0]),float(ts[1])+0.1,float(ts[2]))

    model_dict = get_reconstruction_model_dict(model)

    rotation_model = pygplates.RotationModel([str('%s/%s/%s' %
        (settings.MODEL_STORE_DIR,model,rot_file)) for rot_file in model_dict['RotationFile']])

    # Create the motion path feature
    digitisation_time = 0
    #seed_points_at_digitisation_time = pygplates.MultiPointOnSphere([SeedPoint])
    motion_path_feature = pygplates.Feature.create_motion_path(
            seed_points_at_digitisation_time,
            times = times,
            valid_time=(2000, 0),
            relative_plate=int(RelativePlate),
            reconstruction_plate_id = int(MovingPlate))

    # Create the shape of the motion path
    #reconstruction_time = 0
    reconstructed_motion_paths = []
    pygplates.reconstruct(
            motion_path_feature, rotation_model, reconstructed_motion_paths, float(reconstruction_time),
            reconstruct_type=pygplates.ReconstructType.motion_path)

    data = {"type": "FeatureCollection"}
    data["features"] = [] 
    for reconstructed_motion_path in reconstructed_motion_paths:
        Dist = []
        for segment in reconstructed_motion_path.get_motion_path().get_segments():
            Dist.append(segment.get_arc_length()*pygplates.Earth.mean_radius_in_kms)
        feature = {"type": "Feature"}
        feature["geometry"] = {}
        feature["geometry"]["type"] = "Polyline"
        #### NOTE CODE TO FLIP COORDINATES TO 
        feature["geometry"]["coordinates"] = [[(lon,lat) for lat,lon in reconstructed_motion_path.get_motion_path().to_lat_lon_list()]]
        feature["geometry"]["distance"] = Dist
        data["features"].append(feature)

    ret = json.dumps(pretty_floats(data))
    
    #add header for CORS
    #http://www.html5rocks.com/en/tutorials/cors/
    response = HttpResponse(ret, content_type='application/json')
    #TODO:
    response['Access-Control-Allow-Origin'] = '*'
    return response

