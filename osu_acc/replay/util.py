"""
Module for helper methods that calculate certain parameters.
"""

from decimal import Decimal
from math import sqrt


def get_ap():
    """
    Calculates the raw AP of a replay.
    """
    # TODO: Design an algorithm for this.


def get_pp():
    """
    Calculates the raw PP of a replay.
    """
    # TODO: Use some other library.


def get_accuracy(a, b, c, d):
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


def get_circle_radius(circle_size):
    """
    Given a beatmap's CS difficulty, return the circle radius in pixels.
    
    osu! itself uses an abstract osu!pixel type and can be calculated as follows:

    circle_radius = 32 * (1 - 0.7 * (circle_size - 5) / 5)

    The osu!pixel formula used above was retrieved from the following link on 01/16/2019.
    https://osu.ppy.sh/help/wiki/osu!_File_Formats/Osu_(file_format)#circle-size

    Converting to actual screen pixels, we have an adjusted formula:

    circle_radius = (playfield_width / 16) * (1 - 0.7 * (circle_size - 5) / 5)

    The pixel formula used above was retrieved from the following link on 01/16/2019.
    https://www.reddit.com/r/osugame/comments/5gd3dm/whats_the_cspixel_formula/dareob5

    As osu! replay files are stored with dimensions 512x384, we will use 512 as our playfield_width.

    Args:
        circle_size (float): The circle size difficulty setting, ranging from 0.0 to 10.0.

    Returns:
        (float): The radius of the circle.
    """

    return (512 / 16) * (1 - 0.7 * (circle_size - 5) / 5)


def is_cursor_on_note(circle_size, replay_event, hit_object):
    """
    Returns True if the player's cursor is on a beatmap object.

    Calculated using the Pythagorean Theorem.

    Args:
        replay_event (osrparse.ReplayEvent): The current player input.
        hit_object (HitObject): The current hit object.

    Returns:
        (bool)
    """

    r = get_circle_radius(circle_size)
    dx = replay_event.x - hit_object.x
    dy = replay_event.y - hit_object.y

    return sqrt(dx**2 + dy**2) < r


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

    return 150 + 50 * (5 - Decimal(overall_diff)) / 5


def get_hit_errors(cs, hit_window, replay_events, hit_objects):
    """
    Given an input replay play data and its beatmap's hit objects' times,
    return a list of hit errors.

    Args:
        cs (float): The beatmap's circle size difficulty.
        hit_window (float): The hit window. See get_hit_window() for more info.
        replay_events (List(ReplayEvent)): A list of all osrparse.ReplayEvents.
        hit_object_times (List(int)): A list of all hit object times in a beatmap.

    Returns:
        An array containing all hit errors in chronological order.
    """

    hit_errors = []

    i, j, prev_inp_time = 0, 0, 0

    while i < len(replay_events) and j < len(hit_objects):
        # Map each beatmap object with the earliest replay input
        # that falls within the object's hit window.

        # Replays store input times relative to the previous input.
        # Convert to absolute times.
        curr_inp_time = prev_inp_time + replay_events[i].time_since_previous_action
        prev_inp_time = curr_inp_time

        # Hit Object times are represented absolutely.
        curr_obj_time = hit_objects[j].time

        # Store the earliest input within the current object's hit window.
        curr_hit_error = curr_inp_time - curr_obj_time

        if abs(curr_hit_error) < hit_window and is_cursor_on_note(cs, replay_events[i], hit_objects[j]):
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
