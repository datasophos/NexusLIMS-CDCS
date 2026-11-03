"""Persistent settings for the public gallery."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class GallerySettings(models.Model):
    """A single site-wide selection policy."""

    MODES = [
        ("all", "All previewable records"),
        ("curated", "Featured or rated records"),
        ("featured", "Featured only"),
    ]
    selection_mode = models.CharField(max_length=16, choices=MODES, default="all")
    minimum_rating = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
