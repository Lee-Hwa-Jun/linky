from urllib.parse import urlparse

from django.db import models
from django.utils.text import slugify


class ProfileQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Profile(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.FileField(upload_to="avatars/", blank=True)
    background_url = models.URLField(blank=True)
    accent_color = models.CharField(max_length=16, default="#f3b1c6")
    button_radius = models.PositiveIntegerField(default=12, help_text="Radius in pixels for link buttons")
    show_total_clicks = models.BooleanField(default=True, help_text="Show the total click count across all links")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProfileQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial string repr
        return self.name

    def save(self, *args, **kwargs):  # pragma: no cover - deterministic transformation
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Link(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="links")
    label = models.CharField(max_length=150)
    url = models.URLField()
    icon = models.CharField(max_length=80, blank=True, help_text="Optional emoji or icon text")
    icon_image = models.FileField(upload_to="link_icons/", blank=True)
    show_discount_badge = models.BooleanField(
        default=False,
        help_text="Show a 할인 badge on the link",
    )
    show_popular_badge = models.BooleanField(
        default=False,
        help_text="Show an 인기 badge on the link",
    )
    click_count = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "label"]

    def __str__(self) -> str:  # pragma: no cover - trivial string repr
        return f"{self.label} ({self.profile})"

    @property
    def is_icon_image(self) -> bool:
        if self.icon_image:
            return True
        if self.icon:
            parsed = urlparse(self.icon)
            return parsed.scheme in {"http", "https"}
        return False

    @property
    def icon_image_url(self) -> str | None:
        if self.icon_image:
            return self.icon_image.url
        if self.is_icon_image and self.icon:
            return self.icon
        return None
