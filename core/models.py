from django.db import models
from django.contrib.auth.models import User
from django.core.validators import (
    FileExtensionValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db.models import Q


class Profile(models.Model):
    class Role(models.TextChoices):
        CLIENT = "client", "Cliente"
        ARTIST = "artist", "Artista"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    name = models.CharField(max_length=120)
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)]
    )
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=80)
    country = models.CharField(max_length=80, default="Brasil")
    contact = models.CharField(max_length=120)
    education = models.BooleanField(default=False)
    education_place = models.CharField(max_length=160, blank=True)
    styles = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    @property
    def style_list(self):
        return [style.strip() for style in self.styles.split(",") if style.strip()]


class Artwork(models.Model):
    artist = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="artworks"
    )
    title = models.CharField(max_length=160)
    series = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    material = models.CharField(max_length=120)
    technique = models.CharField(max_length=100)
    style = models.CharField(max_length=100)
    width = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    height = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    promotion = models.BooleanField(default=False)
    observations = models.TextField(blank=True)
    image = models.FileField(
        upload_to="artworks/",
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"])
        ],
    )
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.title

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url or ""


class ArtworkLike(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="artwork_likes"
    )
    artwork = models.ForeignKey(
        Artwork, on_delete=models.CASCADE, related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("profile", "artwork"), name="unique_profile_artwork_like"
            )
        ]


class ArtistFollow(models.Model):
    follower = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="artist_follows"
    )
    artist = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="artist_followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("follower", "artist"), name="unique_profile_artist_follow"
            ),
            models.CheckConstraint(
                condition=~Q(follower=models.F("artist")),
                name="cannot_follow_self",
            ),
        ]


class ArtworkInterest(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="artwork_interests"
    )
    artwork = models.ForeignKey(
        Artwork, on_delete=models.CASCADE, related_name="interests"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("profile", "artwork"), name="unique_profile_artwork_interest"
            )
        ]
