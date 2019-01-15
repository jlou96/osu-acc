from decimal import Decimal
import json
import requests
import osrparse as osrp

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


def get_hit_errors():
    """
    Given an input replay, return a list of hit errors.
    """

    hit_errors = []

    # TODO

    return hit_errors


def calc_hit_error_data():
    """
    Calculates various metrics regarding hit errors.

    Args:
        replay_events (List(osrp.ReplayEvent)): A list of all ReplayEvent instances.

    Returns:
        A dictionary containing all relevant hit error metrics.
    """

    data = {}

    # TODO

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

    song_title = data['title']
    song_artist = data['artist']
    beatmap_creator = data['creator']
    beatmap_difficulty = data['version']
    beatmap_od = data['diff_overall']
    play_date = parsed_replay.timestamp

    ap = 0.00
    pp = 0.00

    num_raw_300 = parsed_replay.number_300s
    num_raw_100 = parsed_replay.number_100s
    num_raw_50  = parsed_replay.number_50s
    num_raw_miss = parsed_replay.misses
    raw_accuracy = calc_accuracy(num_raw_300, num_raw_100, num_raw_50, num_raw_miss)
    
    num_true_300 = parsed_replay.number_300s
    num_true_100 = parsed_replay.number_100s
    num_true_50  = parsed_replay.number_50s
    num_true_miss = parsed_replay.misses
    true_accuracy = calc_accuracy(num_true_300, num_true_100, num_true_50, num_true_miss)


    # Create an instance of a Replay model

