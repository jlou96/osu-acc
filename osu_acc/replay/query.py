"""
A module to handle queries on the DB.
"""

from decimal import Decimal
from requests import get

from osu_acc.replay import util
from osu_acc.replay import classes
from osu_acc.replay.models import Replay, ReplayData
from osu_acc.beatmap.models import Beatmap, BreakPeriod, TimingPoint, HitObject


# =============================================================================
# REPLAY MODELS
# =============================================================================

def create_replay_data_entry(replay_id, replay_events):
    """
    Given a list of classes.ReplayEvents, create and save a models.ReplayData instance.

    Args:
        replay_events (List(classes.ReplayEvent)): The replay data.
    """
    if ReplayData.objects.filter(replay_id=replay_id).exists():
        return

    replay_data_fields = {}

    replay_data_fields['replay_id'] = replay_id
    replay_data_fields['x_coords'] = []
    replay_data_fields['y_coords'] = []
    replay_data_fields['hit_object_times'] = []

    for replay_event in replay_events:
        replay_data_fields['x_coords'].append(replay_event.x)
        replay_data_fields['y_coords'].append(replay_event.y)
        replay_data_fields['hit_object_times'].append(replay_event.time)

    replay_data_entry = ReplayData(**replay_data_fields)
    replay_data_entry.save()


def select_replay_data_field(replay_id, field):
    """
    Returns the value of the field of a specific ReplayData entry.

    Equivalent to: SELECT field FROM replay_replaydata WHERE replay_id = replay_id;

    Args:
        replay_id (str): The hash of the replay, given by osrparse.

    Returns:
        field: The field requested.
        Is of type: str, List(Decimal).
    """

    valid_keys = set([
        'x_coords',
        'y_coords',
        'hit_object_times',
    ])

    if field not in valid_keys:
        # Raise a proper exception
        return None

    replay = Replay.objects.get(replay_id=replay_id)
    return getattr(replay, field)


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

    # GETTING ARGUMENTS AND CONVERTING TYPES
    circle_size = Decimal(json_resp['diff_size'])
    overall_diff = Decimal(json_resp['diff_overall'])
    break_periods_model = select_beatmap_field(json_resp['beatmap_id'], 'break_period')
    break_periods = util.convert_beatmap_break_periods_to_class(break_periods_model)
    replay_events = util.convert_osrp_play_data_to_class(parsed_replay.play_data)
    hit_objects_model = select_beatmap_field(json_resp['beatmap_id'], 'hit_object')
    hit_objects = util.convert_hit_object_model_to_class(hit_objects_model)

    # POPULATING FIELD DICTIONARY
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


    true_acc_fields = util.get_true_accuracy_fields(circle_size,
                                                    overall_diff,
                                                    break_periods,
                                                    replay_events,
                                                    hit_objects)
    replay_fields = {**replay_fields, **true_acc_fields}
    replay_fields['true_accuracy'] = util.get_accuracy(replay_fields['num_true_300'],
                                                       replay_fields['num_true_100'],
                                                       replay_fields['num_true_50'],
                                                       replay_fields['num_true_miss'])

    create_replay_data_entry(parsed_replay.replay_hash, replay_events)
    replay_fields['replay_data'] = ReplayData.objects.get(replay_id=parsed_replay.replay_hash)

    replay_fields['hit_errors'] = util.get_hit_errors(circle_size,
                                                      overall_diff,
                                                      break_periods,
                                                      replay_events,
                                                      hit_objects)

    hit_error_data = util.calc_hit_error_data(replay_fields['hit_errors'])
    replay_fields = {**replay_fields, **hit_error_data}

    # Create an instance of a Replay model
    replay_entry = Replay(**replay_fields)
    replay_entry.save()


def select_replay_field(replay_id, field):
    """
    Returns the value of the field of a specific Replay entry.

    Equivalent to: SELECT field FROM replay_replay WHERE replay_id = replay_id;

    Args:
        replay_id (str): The hash of the replay, given by osrparse.

    Returns:
        query_set[field]: The field requested.
        Is of type: str, Beatmap, DateTime, Decimal, int, List(Decimal)
    """

    valid_keys = set([
        'beatmap',
        'replay_data',
        'play_date',
        'pp',
        'raw_accuracy',
        'num_raw_300',
        'num_raw_100',
        'num_raw_50',
        'num_raw_miss',
        'ap',
        'true_accuracy',
        'num_true_300',
        'num_true_100',
        'num_true_50',
        'num_true_miss',
        'hit_errors',
        'min_neg_hit_error',
        'max_neg_hit_error',
        'avg_neg_hit_error',
        'min_pos_hit_error',
        'max_pos_hit_error',
        'avg_pos_hit_error',
        'min_abs_hit_error',
        'max_abs_hit_error',
        'avg_abs_hit_error',
    ])

    if field not in valid_keys:
        # Raise a proper exception
        return None

    replaydata = ReplayData.objects.get(replay_id=replay_id)
    return getattr(replaydata, field)


# =============================================================================
# BEATMAP MODELS
# =============================================================================


def create_break_period_entry(bm_id, data):
    """
    Create and save a BreakPeriod entry.

    Equivalent to: INSERT INTO beatmap_breakperiod (fields) VALUES (values);

    Args:
        bm_id (str): The id of the beatmap associated.
        data (List(str)): The beatmap data as a list of strings.

    Returns:
        break_period_entry(BreakPeriod): The created BreakPeriod instance.
    """

    if BreakPeriod.objects.filter(beatmap_id=bm_id).exists():
        return

    # Syntax: 2,start,end
    # The start and end fields are both an integral number of milliseconds,
    # from the beginning of the song,
    # defining the start and end point of the break period, respectively.

    break_fields = {}
    break_fields['beatmap_id'] = bm_id
    break_fields['starts'] = []
    break_fields['ends'] = []

    is_break = False

    for line in data:
        if 'Break Periods' in line.strip():
            is_break = True
            continue

        if is_break:
            # Next subsection, storyboarding, begins with the line
            # '//Storyboard Layer 0 (Background)\n'
            if 'Storyboard' in line.strip():
                is_break = False
            else:
                start = int(line.split(',')[1])
                break_fields['starts'].append(start)
                end = int(line.split(',')[2])
                break_fields['ends'].append(end)

    break_entry = BreakPeriod(**break_fields)
    break_entry.save()


def select_break_period_field(beatmap_id, field):
    """
    Returns the value of the field of a specific Break entry.

    Equivalent to: SELECT field FROM beatmap_break WHERE beatmap_id = beatmap_id;

    Args:
        beatmap_id (str): The id of the beatmap, given by osu!api.

    Returns:
        field: The field requested.
        Is of type: List(int), List(Decimal).
    """

    valid_keys = set(['starts', 'ends'])

    if field not in valid_keys:
        # TODO: Raise a proper exception.
        return None

    break_period = BreakPeriod.objects.get(beatmap_id=beatmap_id)
    return getattr(break_period, field)


def create_timing_point_entry(bm_id, data):
    """
    Create and save a TimingPoint entry.

    Equivalent to: INSERT INTO beatmap_timingpoint (fields) VALUES (values);

    Args:
        bm_id (str): The id of the beatmap associated.
        data (List(str)): The beatmap data as a list of strings.

    Returns:
        timing_point_model(TimingPoint): The created TimingPoint instance.
    """
    if TimingPoint.objects.filter(beatmap_id=bm_id).exists():
        return

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

    timing_point_entry = TimingPoint(**timing_point_fields)
    timing_point_entry.save()


def select_timing_point_field(beatmap_id, field):
    """
    Returns the value of the field of a specific TimingPoint entry.

    Equivalent to: SELECT field FROM beatmap_timingpoint WHERE beatmap_id = beatmap_id;

    Args:
        beatmap_id (str): The id of the beatmap, given by osu!api.

    Returns:
        field: The field requested.
        Is of type: List(int), List(Decimal).
    """

    valid_keys = set([
        'offsets',
        'ms_per_beats',
    ])

    if field not in valid_keys:
        # Raise a proper exception
        return None

    timingpoint = TimingPoint.objects.get(beatmap_id=beatmap_id)
    return getattr(timingpoint, field)


def create_hit_object_entry(bm_id, data):
    """
    Create and save a HitObject entry.

    Equivalent to: INSERT INTO beatmap_hitobject (fields) VALUES (values);

    Args:
        bm_id (str): The id of the beatmap associated.
        data (List(str)): The beatmap data as a list of strings.

    Returns:
        hit_object_model(HitObject): The created HitObject instance.
    """
    if HitObject.objects.filter(beatmap_id=bm_id).exists():
        return

    # Syntax: x,y,time,type,hitSound...,extras
    # For our purposes, we only need the time field
    hit_object_fields = {}
    hit_object_fields['beatmap_id'] = bm_id
    hit_object_fields['x_coords'] = []
    hit_object_fields['y_coords'] = []
    hit_object_fields['hit_object_times'] = []
    hit_object_fields['hit_object_types'] = []

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
                obj_time = line.split(',')[2]
                hit_object_fields['hit_object_times'].append(obj_time)
                obj_type = line.split(',')[3]
                hit_object_fields['hit_object_types'].append(obj_type)

    hit_object_entry = HitObject(**hit_object_fields)
    hit_object_entry.save()


def select_hit_object_field(beatmap_id, field):
    """
    Returns the value of the field of a specific HitObject entry.

    Equivalent to: SELECT field FROM beatmap_hitobject WHERE beatmap_id = beatmap_id;

    Args:
        beatmap_id (str): The id of the beatmap, given by osu!api.

    Returns:
        field: The field requested.
        Is of type: List(Decimal).
    """

    valid_keys = set([
        'x_coords',
        'y_coords',
        'hit_object_times',
    ])

    if field not in valid_keys:
        # Raise a proper exception
        return None

    hitobject = HitObject.objects.get(beatmap_id=beatmap_id)
    return getattr(hitobject, field)


def create_beatmap_entry(json_resp):
    """
    Given a beatmap's API response as JSON,
    populate the database with the appropriate information.

    Args:
        json_resp (dict): The response from osu!api
    """
    bm_id = json_resp['beatmap_id']

    if Beatmap.objects.filter(beatmap_id=bm_id).exists():
        return

    # Download beatmap file
    OSU_BEATMAP_ENDPOINT = 'https://osu.ppy.sh/osu/'
    response = get(OSU_BEATMAP_ENDPOINT + bm_id)

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

    # Create and get model fields
    create_break_period_entry(bm_id, data)
    beatmap_fields['break_period'] = BreakPeriod.objects.get(beatmap_id=bm_id)
    create_timing_point_entry(bm_id, data)
    beatmap_fields['timing_point'] = TimingPoint.objects.get(beatmap_id=bm_id)
    create_hit_object_entry(bm_id, data)
    beatmap_fields['hit_object'] = HitObject.objects.get(beatmap_id=bm_id)

    # Create Beatmap model instance and save to DB
    beatmap_entry = Beatmap(**beatmap_fields)
    beatmap_entry.save()


def select_beatmap_field(beatmap_id, field):
    """
    Returns the value of the field of a specific Beatmap entry.

    Equivalent to: SELECT field FROM beatmap_beatmap WHERE beatmap_id = beatmap_id;

    Args:
        beatmap_id (str): The id of the beatmap, given by osu!api.

    Returns:
        field: The field requested.
        Is of type: TimingPoint, HitObject, str, Decimal.
    """

    valid_keys = set([
        'break_period',
        'timing_point',
        'hit_object',
        'beatmap_creator',
        'beatmap_difficulty',
        'beatmap_cs',
        'beatmap_od',
        'song_title',
        'song_artist',
    ])

    if field not in valid_keys:
        # Raise a proper exception
        return None

    beatmap = Beatmap.objects.get(beatmap_id=beatmap_id)
    return getattr(beatmap, field)
