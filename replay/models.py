from django.db import models
from django.contrib.postgres.fields import ArrayField


class Replay(models.Model):
    # METADATA
    song_title = models.CharField(max_length=32)
    song_artist = models.CharField(max_length=32)
    beatmap_creator = models.CharField(max_length=16)
    beatmap_difficulty = models.CharField(max_length=32)
    beatmap_od = models.DecimalField(max_digits=3, decimal_places=1)
    rank_achieved = models.CharField(max_length=1)

    # STANDARD DATA
    pp = models.DecimalField(max_digits=6, decimal_places=2)
    raw_accuracy = models.DecimalField(max_digits=4, decimal_places=2)
    count_300 = models.PositiveSmallIntegerField()
    count_100 = models.PositiveSmallIntegerField()
    count_50 = models.PositiveSmallIntegerField()
    count_miss = models.PositiveSmallIntegerField()

    # EXTRA DATA
    ap = models.DecimalField(max_digits=6, decimal_places=2)
    true_accuracy = models.DecimalField(max_digits=4, decimal_places=2)

    # ArrayField is PostGreSQL only!
    hit_error_array = ArrayField(models.DecimalField(max_digits=5, decimal_places=2))

    min_early_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    max_early_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    mean_early_hit_error = models.DecimalField(max_digits=5, decimal_places=2)

    min_late_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    max_late_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    mean_late_hit_error = models.DecimalField(max_digits=5, decimal_places=2)

    min_abs_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    max_abs_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    mean_abs_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
