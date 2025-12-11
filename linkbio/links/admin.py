from django.contrib import admin

from .models import Link, Profile


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1
    fields = ("label", "url", "icon", "is_primary", "order")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "headline")
    inlines = [LinkInline]


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("label", "profile", "is_primary", "order")
    list_filter = ("is_primary", "profile")
    search_fields = ("label", "url")
    ordering = ("profile", "order")
