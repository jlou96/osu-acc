from django.db import models
from django.contrib.postgres.fields import ArrayField


class Beatmap(models.Model):
    # PRIMARY KEY
    beatmap_id = models.CharField(max_length=64)

    # METADATA
    song_title = models.CharField(max_length=32)
    song_artist = models.CharField(max_length=32)
    beatmap_creator = models.CharField(max_length=16)
    beatmap_difficulty = models.CharField(max_length=32)
    beatmap_od = models.DecimalField(max_digits=3, decimal_places=1)

    # OBJECT HIT TIMES
    timing_point_offsets = ArrayField(models.IntegerField())
    timing_point_ms_per_beats = ArrayField(models.DecimalField(max_digits=9, decimal_places=2))
    object_hit_times = ArrayField(models.IntegerField())
