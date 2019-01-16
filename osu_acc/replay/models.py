from django.db import models
from django.contrib.postgres.fields import ArrayField

from ..beatmap.models import Beatmap


class Replay(models.Model):
    # PRIMARY KEY
    replay_id = models.CharField(max_length=64, primary_key=True)

    # FOREIGN KEYS
    beatmap = models.ForeignKey(Beatmap, on_delete=models.CASCADE, verbose_name='The related beatmap')

    play_date = models.DateTimeField()

    # STANDARD DATA
    pp = models.DecimalField(max_digits=6, decimal_places=2)
    raw_accuracy = models.DecimalField(max_digits=4, decimal_places=2)
    num_raw_300 = models.PositiveSmallIntegerField()
    num_raw_100 = models.PositiveSmallIntegerField()
    num_raw_50 = models.PositiveSmallIntegerField()
    num_miss = models.PositiveSmallIntegerField()

    # EXTRA DATA
    ap = models.DecimalField(max_digits=6, decimal_places=2)
    true_accuracy = models.DecimalField(max_digits=4, decimal_places=2)
    num_true_300 = models.PositiveSmallIntegerField()
    num_true_100 = models.PositiveSmallIntegerField()
    num_true_50 = models.PositiveSmallIntegerField()
    num_true_miss = models.PositiveSmallIntegerField()

    # ArrayField is PostGreSQL only!
    hit_inputs = ArrayField(models.IntegerField())
    hit_errors = ArrayField(models.DecimalField(max_digits=5, decimal_places=2))

    min_neg_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    max_neg_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    avg_neg_hit_error = models.DecimalField(max_digits=5, decimal_places=2)

    min_pos_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    max_pos_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    avg_pos_hit_error = models.DecimalField(max_digits=5, decimal_places=2)

    min_abs_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    max_abs_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
    avg_abs_hit_error = models.DecimalField(max_digits=5, decimal_places=2)
