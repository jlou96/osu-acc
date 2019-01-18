"""
A module that contains handler functions, typically called from a view.
"""

from secrets import OSU_API_KEY

import requests
import osrparse as osrp

from osu_acc.replay.models import Replay
from osu_acc.beatmap.models import Beatmap
import osu_acc.replay.query as query

# =============================================================================
# CONSTANTS
# =============================================================================

OSU_API_ENDPOINT = 'https://osu.ppy.sh/api/get_beatmaps'


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
        query.create_beatmap_entry(json_resp)
    
    query.create_replay_entry(json_resp, parsed_replay)

    return parsed_replay.replay_hash
