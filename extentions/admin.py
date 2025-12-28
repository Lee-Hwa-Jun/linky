from django.contrib import admin

from .models import Extension, Inquiry


@admin.register(Extension)
class ExtensionAdmin(admin.ModelAdmin):
    list_display = ("name", "summary", "install_url", "created_at")
    search_fields = ("name", "summary")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("title", "extension", "category", "ip_address", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "content", "ip_address")
