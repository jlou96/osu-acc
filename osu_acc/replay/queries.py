from decimal import Decimal
import requests
import osrparse as osrp

from ..replay.models import Replay
from ..beatmap.models import Beatmap
from settings_secret import OSU_API_KEY

OSU_API_ENDPOINT = 'https://osu.ppy.sh/api/get_beatmaps'


def calc_ap():
    """
    Calculates the raw AP of a replay.
    """
    # TODO: Design an algorithm for this.
    pass


def calc_pp():
    """
    Calculates the raw PP of a replay.
    """
    # TODO: Use some other library.
    pass


def calc_accuracy(a, b, c, d):
    """
    Calculates the accuracy of a replay.
    Returns raw or true accuracy depending on input.

    Args:
        a (int): The number of 300s.
        b (int): The number of 100s.
        c (int): The number of 50s.
        d (int): The number of misses.

    Returns:
        The accuracy, a floating point number with 2 decimal places.
    """
    numer = 300*a + 100*b + 50*c
    denom = 300*(a + b + c + d)
    raw = Decimal(numer/denom)

    return round(raw, 2)


def create_beatmap_entry(data):
    """
    Given a beatmap's API response as JSON, populate the database with the appropriate information.
    """
    bm_id = data['beatmap_id']

    if Beatmap.objects.filter(beatmap_id=bm_id):
        return

    # Download beatmap file
    OSU_BEATMAP_ENDPOINT = 'https://osu.ppy.sh/osu/'
    response = requests.get(OSU_BEATMAP_ENDPOINT + bm_id)

    with open(bm_id + '.osu', 'wb') as f:
        f.write(response.content)
        data = f.readlines()

    # Parse beatmap file for required data
    beatmap_fields = {}

    beatmap_fields['beatmap_id'] = bm_id

    beatmap_fields['song_title'] = data['title']
    beatmap_fields['song_artist'] = data['artist']
    beatmap_fields['beatmap_creator'] = data['creator']
    beatmap_fields['beatmap_difficulty'] = data['version']
    beatmap_fields['beatmap_od'] = data['diff_overall']

    beatmap_fields['timing_point_offsets'] = []
    beatmap_fields['timing_point_ms_per_beats'] = []
    beatmap_fields['hit_object_times'] = []

    # Timing Points
    # Syntax: Offset, Milliseconds per Beat, Meter, 
    #         Sample Set, Sample Index, Volume, Inherited, Kiai Mode
    # For our purposes, we only need the first three fields.
    # We will also convert all ms/beat values to positive.

    for line in data:
        if line.strip() == '[TimingPoints]':
            is_timing_point = True
            continue
        
        if is_timing_point:
            # There is always an empty line before the start of the next section
            # Use it to identify when the current section ends
            if not line.strip():
                is_timing_point = False
            else:
                beatmap_fields['timing_point_offsets'].append(int(line.split(',')[0]))
                beatmap_fields['timing_point_ms_per_beats'].append(Decimal(line.split(',')[1]))

    # HitObjects
    # Syntax: x,y,time,type,hitSound...,extras
    # For our purposes, we only need the time field

    for line in data:
        if line.strip() == '[HitObjects]':
            is_hit_object = True
            continue

        if is_hit_object:
            if not line.strip():
                is_hit_object = False
            else:
                hit_object_time = line.split(',')[2]
                beatmap_fields['hit_object_times'].append(int(hit_object_time))
    
    # Create Beatmap model instance and save to DB
    beatmap_model = Beatmap(**beatmap_fields)
    beatmap_model.save()


def get_beatmap_hit_times(bm_id):
    """
    Returns a list of integers representing the object hit times of the beatmap.

    Equivalent to: SELECT object_hit_times FROM Beatmaps WHERE beatmap_id=bm_id

    Args:
        bm_id (str): The ID of the beatmap, given by the osu!api.
    
    Returns:
        beatmap_hit_times (List(int)): The object hit times of the beatmap.
    """

    beatmap_hit_times = Beatmap.objects.values_list('object_hit_times', flat=True).get(beatmap_id=bm_id)
    return beatmap_hit_times


def get_hit_window(overall_diff):
    """
    Returns the maximum amount of time, in milliseconds, that an input candeivate
    from a beatmap's hit object time in order to count as a hit.

    The formula used was retrieved from the following link on 01/15/2019.
    https://osu.ppy.sh/help/wiki/osu!_File_Formats/Osu_(file_format)#overall-difficulty

    Args:
        od (float): The beatmap's overall difficulty.
    
    Returns:
        A float.
    """

    return 150 + 50 * (5 - overall_diff) / 5


def get_hit_errors(hit_window, replay_events, hit_object_times):
    """
    Given an input replay play data and its beatmap's hit objects' times,
    return a list of hit errors.

    Args:
        hit_window (float): The hit window. See get_hit_window() for more info.
        replay_events (List(ReplayEvent)): A list of all osrparse.ReplayEvents.
        hit_object_times (List(int)): A list of all hit object times in a beatmap.

    Returns:
        An array containing all hit errors in chronological order.
    """

    hit_errors = []

    i, j, prev_obj_time = 0, 0, 0

    while i < len(replay_events) and j < len(hit_object_times):
        # Map each beatmap object with the earliest replay input
        # that falls within the object's hit window.

        # Replays store input times relative to the previous input.
        curr_inp_time = replay_events[i].time_since_previous_action

        # Hit Object times are represented absolutely,
        # so we must convert this value to be relative.
        curr_obj_time = hit_object_times[j] - prev_obj_time
        prev_obj_time = hit_object_times[j]

        # Store the earliest input within the current object's hit window.
        curr_hit_error = curr_obj_time - curr_inp_time

        if abs(curr_hit_error) < hit_window:
            hit_errors.append(curr_hit_error)

            j += 1

        i += 1

    return hit_errors


def calc_hit_error_data(hit_errors):
    """
    Calculates various metrics regarding hit errors.

    Args:
        hit_errors (List(float)): A list of all hit errors.

    Returns:
        A dictionary containing all relevant hit error metrics.
    """

    data = {}

    pos_errors, neg_errors, abs_errors = [], [], []

    for error in hit_errors:
        if error > 0:
            pos_errors.append(error)
        elif error < 0:
            neg_errors.append(error)
        abs_errors.append(abs(error))
    
    data['min_pos'] = min(pos_errors)
    data['max_pos'] = max(pos_errors)
    data['avg_pos'] = sum(pos_errors) / len(pos_errors)

    data['min_neg'] = min(neg_errors)
    data['max_neg'] = max(neg_errors)
    data['avg_neg'] = sum(neg_errors) / len(neg_errors)

    data['min_abs'] = min(abs_errors)
    data['max_abs'] = max(abs_errors)
    data['avg_abs'] = sum(abs_errors) / len(abs_errors)

    data['num_pos'] = len(pos_errors)
    data['num_neg'] = len(neg_errors)

    return data


def handle_replay(replay):
    """
    Given an uploaded osu! replay file, retrieve the data
    necessary to create a Replay model and write it to DB.

    Args:
        replay: A replay file.

    Returns:
        Nothing.
    """

    # Parse the local replay file and extract data
    parsed_replay = osrp.parse_replay_file(replay)
    beatmap_hash  = parsed_replay.beatmap_hash
    replay_events = parsed_replay.play_data

    # Make a call to osu!api to request beatmap metadata
    payload  = {'k': OSU_API_KEY, 'h': beatmap_hash}
    response = requests.get(OSU_API_ENDPOINT, payload)

    # Returns a JSON list with one element containing our beatmap info
    data = response.json()[0]

    # If the song is longer than 999,999.99ms (16m 40s), reject
    if data['total_length'] >= 1000:
        # TODO: Write a proper exception for this.
        print('Do not replays of maps longer than 16:40.')
        return

    # If there a Beatmap model of this Replay's beatmap does not exist, create it
    bm_id = data['beatmap_id']

    if not Beatmap.objects.filter(beatmap_id=bm_id):
        create_beatmap_entry(data) 

    # Create and populate dictionary containing all fields in the Replay model
    replay_fields = {}

    replay_fields['play_date'] = parsed_replay.timestamp

    replay_fields['ap'] = 0.00
    replay_fields['pp'] = 0.00

    replay_fields['num_raw_300'] = parsed_replay.number_300s
    replay_fields['num_raw_100'] = parsed_replay.number_100s
    replay_fields['num_raw_50']  = parsed_replay.number_50s
    replay_fields['num_raw_miss'] = parsed_replay.misses
    replay_fields['raw_accuracy'] = calc_accuracy(replay_fields['num_raw_300'], replay_fields['num_raw_100'],
                                                  replay_fields['num_raw_50'], replay_fields['num_raw_miss'])
    
    replay_fields['num_true_300'] = parsed_replay.number_300s
    replay_fields['num_true_100'] = parsed_replay.number_100s
    replay_fields['num_true_50']  = parsed_replay.number_50s
    replay_fields['num_true_miss'] = parsed_replay.misses
    replay_fields['true_accuracy'] = calc_accuracy(replay_fields['num_true_300'], replay_fields['num_true_100'],
                                                   replay_fields['num_true_50'], replay_fields['num_true_miss'])

    hit_window = get_hit_window(data['diff_overall'])
    hit_object_times = get_beatmap_hit_times(bm_id)
    replay_fields['hit_errors'] = get_hit_errors(hit_window, replay_events, hit_object_times)

    hit_error_data = calc_hit_error_data(replay_fields['hit_errors'])

    replay_fields['min_neg_hit_error'] = hit_error_data['min_neg']
    replay_fields['max_neg_hit_error'] = hit_error_data['max_neg']
    replay_fields['avg_neg_hit_error'] = hit_error_data['avg_neg']

    replay_fields['min_pos_hit_error'] = hit_error_data['min_pos']
    replay_fields['max_pos_hit_error'] = hit_error_data['max_pos']
    replay_fields['avg_pos_hit_error'] = hit_error_data['avg_pos']

    replay_fields['min_abs_hit_error'] = hit_error_data['min_abs']
    replay_fields['max_abs_hit_error'] = hit_error_data['max_abs']
    replay_fields['avg_abs_hit_error'] = hit_error_data['avg_abs']

    # Create an instance of a Replay model
    replay_model = Replay(**replay_fields)
    replay_model.save()
