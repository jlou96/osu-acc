"""
Module for helper methods that calculate certain parameters or other stuff.
"""

from decimal import Decimal
from math import sqrt

from osu_acc.replay import classes


# =============================================================================
# CONVERSION METHODS
# =============================================================================


def convert_beatmap_break_periods_to_class(break_model):
    """
    Converts a BreakPeriod model to a list of BreakPeriod class instances.
    """

    break_periods = []

    size = len(break_model.starts)

    for i in range(size):
        start = break_model.starts[i]
        end = break_model.ends[i]

        break_periods.append(classes.BreakPeriod(start, end))

    return break_periods


def convert_osrp_play_data_to_class(play_data):
    """
    Converts a list of osrparse.ReplayEvents to a list of replay.classes.ReplayEvents.

    Args:
        play_data (List(osrparse.ReplayEvent)): osrparse.ReplayEvents.

    Returns:
        replay_events (List(classes.ReplayEvent)): A list of ReplayEvent instances.
    """

    replay_events = []
    size = len(play_data)

    time_elapsed = 0

    for i in range(size):
        x = play_data[i].x
        y = play_data[i].y
        time_elapsed += play_data[i].time_since_previous_action
        time = time_elapsed

        replay_events.append(classes.ReplayEvent(x, y, time))

    return replay_events


def convert_hit_object_model_to_class(hit_object_model):
    """
    Converts a HitObject model to a list of HitObject class instances.

    Args:
        hit_object_models (beatmap.models.HitObject): An instance of the HitObject model.

    Returns:
        hit_objects (List(classes.HitObject)): A list of HitObject class instances.
    """

    hit_objects = []
    size = len(hit_object_model.hit_object_times)

    for i in range(size):
        x = hit_object_model.x_coords[i]
        y = hit_object_model.y_coords[i]
        obj_time = hit_object_model.hit_object_times[i]
        obj_type = hit_object_model.hit_object_types[i]

        hit_objects.append(classes.HitObject(x, y, obj_time, obj_type))

    return hit_objects


# =============================================================================
# CALCULATION METHODS
# =============================================================================


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
    try:
        raw = 100 * Decimal(numer/denom)
    except ZeroDivisionError:
        raw = 0.00

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

    As osu! replay files have dimensions 512x384, and 512/16 == 32, we will use that instead.

    Args:
        circle_size (float): The circle size difficulty setting, ranging from 0.0 to 10.0.

    Returns:
        (float): The radius of the circle.
    """

    return 32 * (1 - Decimal(0.7) * (circle_size - 5) / 5)


def is_cursor_on_note(circle_size, replay_event, hit_object):
    """
    Returns True if the player's cursor is on a beatmap object.

    Calculated using the Pythagorean Theorem.

    Args:
        replay_event (classes.ReplayEvent): The current player input.
        hit_object (classes.HitObject): The current hit object.

    Returns:
        Whether the cursor is within the circle or not.
    """

    r = get_circle_radius(circle_size)
    dx = replay_event.x - hit_object.x
    dy = replay_event.y - hit_object.y

    return sqrt(dx**2 + dy**2) < r


def associate_hits(mode, circle_size, overall_diff, break_periods, replay_events, hit_objects):
    """
    Returns a list of tuples, associating a ReplayEvent with a HitObject

    Args:
        mode (str): Either 'raw' or 'true'.
        circle_size (Decimal): The beatmap's circle size.
        overall_diff (Decimal): The beatmap's overall difficulty.
        break_periods (List(BreakPeriod)): A list of all break periods in a beatmap.
        replay_events (List(ReplayEvent)): A list of all osrparse.ReplayEvents.
        hit_object (List(HitObject)): A list of all hit object in a beatmap.

    Returns:
        associations (List(tuple)): A list of associations.
        Each association is a 3-tuple of the form (ReplayEvent, HitObject, hit_error)
    """

    print('associate_hits() called')

    valid_modes = set(['raw', 'true'])

    if mode not in valid_modes:
        # TODO: Raise a proper exception.
        print('Error: Invalid mode {m} passed to associate_hits()'.format(m=mode))
        return

    associations = []
    hit_window = get_hit_window(overall_diff, '50')

    # Associate each hit object with the earliest replay input
    # that falls within the object's hit window.
    for hit_object in hit_objects:
        is_note_associated = False
        is_note_hit = False
        is_note_attempted = False

        # Spinners do not meaningfully affect accuracy,
        # and thus will not be associated.
        if hit_object.is_spinner:
            print('HitObject is a spinner.')
            continue

        for replay_event in replay_events:
            # If current replay input is within a break,
            # then continue to the next input.
            for break_period in break_periods:
                if replay_event.time in range(break_period.start, break_period.end+1):
                    print('ReplayEvent at {t1} within break period {t2} - {t3}'.format(t1=replay_event.time, t2=break_period.start, t3=break_period.end))
                    continue

            curr_inp_time = replay_event.time
            curr_obj_time = hit_object.time
            curr_hit_error = curr_inp_time - curr_obj_time

            if curr_hit_error > hit_window:
                print('Current hit error of {he} exceeds hit window of {hw}'.format(he=curr_hit_error, hw=hit_window))
                break

            if abs(curr_hit_error) <= hit_window:
                # Set flags
                is_note_attempted = True
                is_note_hit = is_cursor_on_note(circle_size, replay_event, hit_object)

                # Make association and append
                curr = classes.Association(replay_event, hit_object, curr_hit_error)
                associations.append(curr)

            if (mode == 'raw' and is_note_hit) or (mode == 'true' and is_note_attempted):
                print('Associated ReplayEvent at {t1} with HitObject at {t2}'.format(t1=replay_event.time, t2=hit_object.time))
                curr = classes.Association(replay_event, hit_object, curr_hit_error)
                associations.append(curr)
                is_note_associated = True
            else:
                print('Did not associate ReplayEvent at {t1} with HitObject at {t2}'.format(t1=replay_event.time, t2=hit_object.time))

            replay_event_counter += 1

        if not is_note_associated:
            print('Did not associate HitObject at {t} with any ReplayEvent'.format(t=hit_object.time))
            curr = classes.Association(None, hit_object, None)
            associations.append(curr)
        print('')

    return associations


def get_true_accuracy_fields(circle_size, overall_diff, break_periods, replay_events, hit_objects):
    """
    Returns the number of true 300s, 100s, 50s and misses as a dictionary.

    Args:
        circle_size (Decimal): The beatmap's circle size difficulty.
        overall_diff (Decimal): The beatmap's overall difficulty.
        break_periods (List(BreakPeriod)): A list of all break periods in a beatmap.
        replay_events (List(classes.ReplayEvent)): A list of all replay events.
        hit_object (List(classes.HitObject)): A list of all hit object in a beatmap.

    Returns:
        fields (dict): A dictionary containing the number of each hit type.
    """

    fields = {}
    fields['num_true_300'] = 0
    fields['num_true_100'] = 0
    fields['num_true_50'] = 0
    fields['num_true_miss'] = 0

    perf_window = get_hit_window(overall_diff, '300')
    good_window = get_hit_window(overall_diff, '100')
    bad_window = get_hit_window(overall_diff, '50')

    associations = associate_hits('true', circle_size, overall_diff,
                                  break_periods, replay_events, hit_objects)

    for association in associations:
        if association.hit_error is None:
            fields['num_true_miss'] += 1
        elif abs(association.hit_error) <= perf_window:
            fields['num_true_300'] += 1
        elif abs(association.hit_error) <= good_window:
            fields['num_true_100'] += 1
        elif abs(association.hit_error) <= bad_window:
            fields['num_true_50'] += 1

    return fields


def get_hit_window(overall_diff, score):
    """
    Returns the maximum amount of time, in milliseconds, that an input candeivate
    from a beatmap's hit object time in order to count as a hit.

    The formula used was retrieved from the following link on 01/15/2019.
    https://osu.ppy.sh/help/wiki/osu!_File_Formats/Osu_(file_format)#overall-difficulty

    Args:
        od (Decimal): The beatmap's overall difficulty.
        score (str): The score.

    Returns:
        (float) The hit window.
    """

    hit_window = None
    valid_scores = set(['300', '100', '50'])

    if score not in valid_scores:
        # TODO: Raise a proper exception.
        return None

    if score == '300':
        hit_window = Decimal(50 + 30 * (5 - overall_diff) / 5)
    if score == '100':
        hit_window = Decimal(100 + 40 * (5 - overall_diff) / 5)
    if score == '50':
        hit_window = Decimal(150 + 50 * (5 - overall_diff) / 5)

    return hit_window


def get_hit_errors(circle_size, overall_diff, break_periods, replay_events, hit_objects):
    """
    Given an input replay play data and its beatmap's hit objects' times,
    return a list of hit errors.

    Args:
        circle_size (Decimal): The beatmap's circle size difficulty.
        overall_diff (Decimal): The beatmap's overall difficulty.
        break_periods (List(BreakPeriod)): A list of all break periods in a beatmap.
        replay_events (List(classes.ReplayEvent)): A list of all replay events.
        hit_object (List(classes.HitObject)): A list of all hit object in a beatmap.

    Returns:
        An array containing all hit errors in chronological order.
    """

    associations = associate_hits('raw', circle_size, overall_diff,
                                  break_periods, replay_events, hit_objects)

    return [association.hit_error for association in associations]


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

    # Just for now...
    if not pos_errors:
        pos_errors.append(Decimal(1.00))
    if not neg_errors:
        neg_errors.append(Decimal(-1.00))
    if not abs_errors:
        abs_errors.append(Decimal(0.00))

    data['min_pos_hit_error'] = min(pos_errors)
    data['max_pos_hit_error'] = max(pos_errors)
    data['avg_pos_hit_error'] = sum(pos_errors) / len(pos_errors)

    data['min_neg_hit_error'] = min(neg_errors)
    data['max_neg_hit_error'] = max(neg_errors)
    data['avg_neg_hit_error'] = sum(neg_errors) / len(neg_errors)

    data['min_abs_hit_error'] = min(abs_errors)
    data['max_abs_hit_error'] = max(abs_errors)
    data['avg_abs_hit_error'] = sum(abs_errors) / len(abs_errors)

    data['num_pos_hit_error'] = len(pos_errors)
    data['num_neg_hit_error'] = len(neg_errors)

    return data
