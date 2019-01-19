"""
A module for shared classes.
"""

from decimal import Decimal


class Association():
    """
    Represents an association between a ReplayEvent and a HitObject.

    If the association is valid, then both hit_object and replay_event
    are instances of their respective classes, as defined below in this module.

    If the association is not valid, then we associate hit_object with None.
    """


    def __init__(self, replay_event, hit_object, hit_error):
        self._replay_event = replay_event
        self._hit_object = hit_object
        self._hit_error = hit_error


    @property
    def replay_event(self):
        return self._replay_event


    @property
    def hit_object(self):
        return self._hit_object


    @property
    def hit_error(self):
        return self._hit_error


class BreakPeriod():
    """
    Represents a break period.
    """


    def __init__(self, start, end):
        self._start = start
        self._end = end


    @property
    def start(self):
        return self._start


    @property
    def end(self):
        return self._end


class ReplayEvent():
    """
    Represents a replay event, but stores time absolutely and ignores key.
    """


    def __init__(self, x, y, time):
        self._x = Decimal(x)
        self._y = Decimal(y)
        self._time = time


    @property
    def x(self):
        return self._x


    @property
    def y(self):
        return self._y


    @property
    def time(self):
        return self._time


class HitObject():
    """
    Represents a hit object.
    """


    def __init__(self, x, y, time, obj_type):
        self._x = Decimal(x)
        self._y = Decimal(y)
        self._time = time
        self._obj_type = obj_type


    @property
    def x(self):
        return self._x


    @property
    def y(self):
        return self._y


    @property
    def time(self):
        return self._time


    # =============================================================================
    # Refer to the "Type" section of the link below
    # https://osu.ppy.sh/help/wiki/osu!_File_Formats/Osu_(file_format)#hit-objects
    # =============================================================================


    def is_circle(self):
        return self._obj_type & 0b1 == 0b1


    def is_slider(self):
        return self._obj_type & 0b11 == 0b10


    def is_spinner(self):
        return self._obj_type & 0b1011 == 0b1000
