"""
A module to handle queries from client.
"""

from decimal import Decimal

import requests
import osrparse as osrp

import osu_acc.replay.util as util
from osu_acc.replay.models import Replay, ReplayData
from osu_acc.beatmap.models import Beatmap, TimingPoint, HitObject
from secrets import OSU_API_KEY

OSU_API_ENDPOINT = 'https://osu.ppy.sh/api/get_beatmaps'


def create_timing_point_entry(bm_id, data):
    """
    Create and save a TimingPoint entry.

    Args:
        bm_id (str): The id of the beatmap associated.
        data (List(str)): The beatmap data as a list of strings.

    Returns:
        timing_point_model(TimingPoint): The created TimingPoint instance.
    """
    if TimingPoint.objects.filter(beatmap_id=bm_id).exists():
        return

    # Timing Points
    # Syntax: Offset, Milliseconds per Beat, Meter, 
    #         Sample Set, Sample Index, Volume, Inherited, Kiai Mode
    # For our purposes, we only need the first three fields.
    # We will also convert all ms/beat values to positive.
    timing_point_fields = {}
    timing_point_fields['beatmap_id'] = bm_id
    timing_point_fields['offsets'] = []
    timing_point_fields['ms_per_beats'] = []

    is_timing_point = False

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
                offset = int(line.split(',')[0])
                timing_point_fields['offsets'].append(offset)
                ms_per_beat = Decimal(line.split(',')[1])
                timing_point_fields['ms_per_beats'].append(round(ms_per_beat, 2))

    timing_point_model = TimingPoint(**timing_point_fields)
    timing_point_model.save()


def create_hit_object_entry(bm_id, data):
    """
    Create and save a HitObject entry.

    Args:
        bm_id (str): The id of the beatmap associated.
        data (List(str)): The beatmap data as a list of strings.

    Returns:
        hit_object_model(HitObject): The created HitObject instance.
    """
    if HitObject.objects.filter(beatmap_id=bm_id).exists():
        return

    # HitObjects
    # Syntax: x,y,time,type,hitSound...,extras
    # For our purposes, we only need the time field
    hit_object_fields = {}
    hit_object_fields['beatmap_id'] = bm_id
    hit_object_fields['x_coords'] = []
    hit_object_fields['y_coords'] = []
    hit_object_fields['hit_object_times'] = []

    is_hit_object = False

    for line in data:
        if line.strip() == '[HitObjects]':
            is_hit_object = True
            continue

        if is_hit_object:
            if not line.strip():
                is_hit_object = False
            else:
                x = line.split(',')[0]
                hit_object_fields['x_coords'].append(x)
                y = line.split(',')[1]
                hit_object_fields['y_coords'].append(y)
                time = line.split(',')[2]
                hit_object_fields['hit_object_times'].append(time)

    hit_object_model = HitObject(**hit_object_fields)
    hit_object_model.save()


def create_beatmap_entry(json_resp):
    """
    Given a beatmap's API response as JSON, populate the database with the appropriate information.
    """
    bm_id = json_resp['beatmap_id']

    if Beatmap.objects.filter(beatmap_id=bm_id).exists():
        return

    # Download beatmap file
    OSU_BEATMAP_ENDPOINT = 'https://osu.ppy.sh/osu/'
    response = requests.get(OSU_BEATMAP_ENDPOINT + bm_id)

    with open(bm_id + '.osu', 'wb') as f:
        f.write(response.content)

    with open(bm_id + '.osu', 'r') as f:
        data = f.readlines()

    # Parse beatmap file for required data
    beatmap_fields = {}

    beatmap_fields['beatmap_id'] = bm_id

    beatmap_fields['song_title'] = json_resp['title']
    beatmap_fields['song_artist'] = json_resp['artist']
    beatmap_fields['beatmap_creator'] = json_resp['creator']
    beatmap_fields['beatmap_difficulty'] = json_resp['version']
    beatmap_fields['beatmap_cs'] = Decimal(json_resp['diff_size'])
    beatmap_fields['beatmap_od'] = Decimal(json_resp['diff_overall'])

    # Create and use TimingPoint and HitObject fields
    create_timing_point_entry(bm_id, data)
    beatmap_fields['timing_point'] = TimingPoint.objects.get(beatmap_id=bm_id)
    create_hit_object_entry(bm_id, data)
    beatmap_fields['hit_object'] = HitObject.objects.get(beatmap_id=bm_id)
    
    # Create Beatmap model instance and save to DB
    beatmap_model = Beatmap(**beatmap_fields)
    beatmap_model.save()


def create_replay_data_entry(parsed_replay):
    """
    Given an osrparse.Replay instance, create and save a ReplayEvent instance.

    Args:
        replay_data (List(osrparse.ReplayEvent)): The replay data.

    Returns:
        (ReplayEvent): A list of hit input times.
    """
    if ReplayData.objects.filter(replay_id=parsed_replay.replay_hash).exists():
        return

    replay_data_fields = {}

    replay_data_fields['replay_id'] = parsed_replay.replay_hash
    replay_data_fields['x_coords'] = []
    replay_data_fields['y_coords'] = []
    replay_data_fields['hit_object_times'] = []

    for replay_event in parsed_replay.play_data:
        replay_data_fields['x_coords'].append(replay_event.x)
        replay_data_fields['y_coords'].append(replay_event.y)
        replay_data_fields['hit_object_times'].append(replay_event.time_since_previous_action)

    replay_data_model = ReplayData(**replay_data_fields)
    replay_data_model.save()


def create_replay_entry(json_resp, parsed_replay):
    """
    Create and save a Replay instance.

    Args:
        json_resp (dict): The result of the osu!api call as a dictionary.
        parsed_replay (osrparse.Replay): The parsed replay.
    """

    if Replay.objects.filter(replay_id=parsed_replay.replay_hash).exists():
        return

    replay_fields = {}

    replay_fields['replay_id'] = parsed_replay.replay_hash
    replay_fields['beatmap'] = Beatmap.objects.get(beatmap_id=json_resp['beatmap_id'])
    replay_fields['play_date'] = parsed_replay.timestamp

    replay_fields['ap'] = 0.00
    replay_fields['pp'] = 0.00

    replay_fields['num_raw_300'] = parsed_replay.number_300s
    replay_fields['num_raw_100'] = parsed_replay.number_100s
    replay_fields['num_raw_50']  = parsed_replay.number_50s
    replay_fields['num_raw_miss'] = parsed_replay.misses
    replay_fields['raw_accuracy'] = util.get_accuracy(replay_fields['num_raw_300'],
                                                      replay_fields['num_raw_100'],
                                                      replay_fields['num_raw_50'],
                                                      replay_fields['num_raw_miss'])
    
    replay_fields['num_true_300'] = parsed_replay.number_300s
    replay_fields['num_true_100'] = parsed_replay.number_100s
    replay_fields['num_true_50']  = parsed_replay.number_50s
    replay_fields['num_true_miss'] = parsed_replay.misses
    replay_fields['true_accuracy'] = util.get_accuracy(replay_fields['num_true_300'],
                                                       replay_fields['num_true_100'],
                                                       replay_fields['num_true_50'],
                                                       replay_fields['num_true_miss'])

    create_replay_data_entry(parsed_replay)
    replay_fields['replay_data'] = ReplayData.objects.get(replay_id=parsed_replay.replay_hash)

    hit_window = util.get_hit_window(Decimal(json_resp['diff_overall']))
    hit_objects = get_beatmap_hit_objects(json_resp['beatmap_id'])
    replay_fields['hit_errors'] = util.get_hit_errors(Decimal(json_resp['diff_size']),
                                                      hit_window,
                                                      parsed_replay.play_data,
                                                      hit_objects)

    hit_error_data = util.calc_hit_error_data(replay_fields['hit_errors'])

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


def get_beatmap_hit_objects(bm_id):
    """
    Returns a list of integers representing the object hit times of the beatmap.

    Equivalent to: SELECT * FROM beatmap_hitobject WHERE beatmap_id = bm_id;

    Args:
        bm_id (str): The ID of the beatmap, given by the osu!api.
    
    Returns:
        beatmap_hit_times (List(int)): The object hit times of the beatmap.
    """

    return HitObject.objects.get(beatmap_id=bm_id)


def get_replay_context(replay_id):
    """
    Returns all the context variables to pass to template given a replay ID.

    Args:
        replay_id (str): The replay ID.

    Returns:
        ctx (dict): The context.
    """

    replay = Replay.objects.get(replay_id=replay_id)

    ctx = {}

    ctx['replay_id'] = replay_id
    ctx['play_date'] = replay.play_date

    ctx['song_artist'] = replay.beatmap.song_artist
    ctx['song_title'] = replay.beatmap.song_title

    ctx['beatmap_id'] = replay.beatmap.beatmap_id
    ctx['beatmap_creator'] = replay.beatmap.beatmap_creator
    ctx['beatmap_cs'] = replay.beatmap.beatmap_cs
    ctx['beatmap_od'] = replay.beatmap.beatmap_od

    ctx['raw_accuracy'] = replay.raw_accuracy
    ctx['num_raw_300'] = replay.num_raw_300
    ctx['num_raw_100'] = replay.num_raw_100
    ctx['num_raw_50'] = replay.num_raw_50
    ctx['num_raw_miss'] = replay.num_raw_miss

    ctx['true_accuracy'] = replay.true_accuracy
    ctx['num_true_300'] = replay.num_true_300
    ctx['num_true_100'] = replay.num_true_100
    ctx['num_true_50'] = replay.num_true_50
    ctx['num_true_miss'] = replay.num_true_miss

    ctx['min_neg_hit_error'] = replay.min_neg_hit_error
    ctx['max_neg_hit_error'] = replay.max_neg_hit_error
    ctx['avg_neg_hit_error'] = replay.avg_neg_hit_error

    ctx['min_pos_hit_error'] = replay.min_pos_hit_error
    ctx['max_pos_hit_error'] = replay.max_pos_hit_error
    ctx['avg_pos_hit_error'] = replay.avg_pos_hit_error

    ctx['min_abs_hit_error'] = replay.min_abs_hit_error
    ctx['max_abs_hit_error'] = replay.max_abs_hit_error
    ctx['avg_abs_hit_error'] = replay.avg_abs_hit_error

    return ctx


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
    parsed_replay = osrp.parse_replay_file(replay.temporary_file_path())
    beatmap_hash  = parsed_replay.beatmap_hash

    # Make a call to osu!api to request beatmap metadata
    payload  = {'k': OSU_API_KEY, 'h': beatmap_hash}
    response = requests.get(OSU_API_ENDPOINT, payload)

    # Returns a JSON list with one element containing our beatmap info
    json_resp = response.json()[0]

    # If the song is longer than 999,999.99ms (16m 40s), reject
    if int(json_resp['total_length']) >= 1000:
        # TODO: Write a proper exception for this.
        print('Do not replays of maps longer than 16:40.')
        return

    # If there a Beatmap model of this Replay's beatmap does not exist, create it
    if not Beatmap.objects.filter(beatmap_id=json_resp['beatmap_id']).exists():
        create_beatmap_entry(json_resp)
    
    create_replay_entry(json_resp, parsed_replay)

    return parsed_replay.replay_hash
