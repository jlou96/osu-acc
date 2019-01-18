"""
A module for shared classes.
"""

from decimal import Decimal


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
