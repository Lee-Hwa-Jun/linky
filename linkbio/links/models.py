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
    avatar_url = models.URLField(blank=True)
    background_url = models.URLField(blank=True)
    accent_color = models.CharField(max_length=16, default="#f3b1c6")
    button_radius = models.PositiveIntegerField(default=12, help_text="Radius in pixels for link buttons")
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
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "label"]

    def __str__(self) -> str:  # pragma: no cover - trivial string repr
        return f"{self.label} ({self.profile})"
