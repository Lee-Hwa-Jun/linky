from django.contrib import admin

from .models import Link, Profile


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1
    fields = (
        "label",
        "url",
        "icon",
        "icon_image",
        "show_discount_badge",
        "show_popular_badge",
        "is_primary",
        "order",
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "show_total_clicks")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "headline")
    fieldsets = (
        (None, {"fields": ("name", "slug", "headline", "bio", "avatar", "background_url")}),
        ("Display", {"fields": ("accent_color", "button_radius", "show_total_clicks", "is_active")}),
    )
    inlines = [LinkInline]


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("label", "profile", "is_primary", "order")
    list_filter = ("is_primary", "profile")
    search_fields = ("label", "url")
    ordering = ("profile", "order")
    fields = (
        "profile",
        "label",
        "url",
        "icon",
        "icon_image",
        "show_discount_badge",
        "show_popular_badge",
        "click_count",
        "is_primary",
        "order",
    )
