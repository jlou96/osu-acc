from django.db import models
from django.contrib.postgres.fields import ArrayField


class TimingPoint(models.Model):
    """
    Represents a timing point.
    """
    # Let Django automatically generate primary key

    # Reference parent Beatmap
    beatmap_id = models.CharField(max_length=64)

    offsets = ArrayField(models.IntegerField())
    ms_per_beats = ArrayField(models.DecimalField(max_digits=9, decimal_places=2))


class HitObject(models.Model):
    """
    Represents a timing point.
    """
    # Let Django automatically generate primary key
    
    # Reference parent Beatmap
    beatmap_id = models.CharField(max_length=64)

    x_coords = ArrayField(models.DecimalField(max_digits=5, decimal_places=2))
    y_coords = ArrayField(models.DecimalField(max_digits=5, decimal_places=2))
    hit_object_times = ArrayField(models.DecimalField(max_digits=9, decimal_places=2))


class Beatmap(models.Model):
    """
    Represents a beatmap.
    """
    # PRIMARY KEY
    beatmap_id = models.CharField(max_length=64, primary_key=True)

    # ONE-TO-ONE
    timing_point = models.OneToOneField(TimingPoint, on_delete=models.CASCADE)
    hit_object = models.OneToOneField(HitObject, on_delete=models.CASCADE)

    # METADATA
    beatmap_creator = models.CharField(max_length=16)
    beatmap_difficulty = models.CharField(max_length=32)
    beatmap_cs = models.DecimalField(max_digits=3, decimal_places=1)
    beatmap_od = models.DecimalField(max_digits=3, decimal_places=1)
    song_title = models.CharField(max_length=128)
    song_artist = models.CharField(max_length=64)
