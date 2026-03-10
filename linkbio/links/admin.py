from django.contrib import admin

from .models import Link, LottoDrawResult, LottoTicket, Profile


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1
    fields = (
        "label",
        "url",
        "icon",
        "icon_image",
        "hashtags",
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
        (
            "소셜 링크",
            {
                "fields": (
                    "instagram_url",
                    "facebook_url",
                    "youtube_url",
                    "thread_url",
                )
            },
        ),
        ("Display", {"fields": ("accent_color", "button_radius", "show_total_clicks", "is_active")}),
    )
    inlines = [LinkInline]


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("label", "profile", "is_primary", "order")
    list_filter = ("is_primary", "profile")
    search_fields = ("label", "url", "hashtags")
    ordering = ("profile", "order")
    fields = (
        "profile",
        "label",
        "url",
        "icon",
        "icon_image",
        "hashtags",
        "show_discount_badge",
        "show_popular_badge",
        "click_count",
        "is_primary",
        "order",
    )


@admin.register(LottoDrawResult)
class LottoDrawResultAdmin(admin.ModelAdmin):
    list_display = ("draw_round", "draw_date_code", "formatted_winning_numbers", "bonus_number", "updated_at")
    search_fields = ("draw_round", "draw_date_code")
    ordering = ("-draw_date",)

    def formatted_winning_numbers(self, obj):
        return ", ".join(str(number) for number in obj.winning_numbers)

    formatted_winning_numbers.short_description = "당첨번호"


@admin.register(LottoTicket)
class LottoTicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "draw_round",
        "draw_date_code",
        "formatted_ticket_numbers",
        "prize_rank",
        "matched_count",
        "matched_bonus",
        "created_at",
    )
    list_filter = ("draw_round", "draw_date", "prize_rank", "matched_bonus")
    search_fields = ("session_key", "draw_date_code", "draw_round")
    readonly_fields = (
        "session_key",
        "client_ip",
        "user_agent",
        "draw_result",
        "matched_numbers",
        "matched_count",
        "matched_bonus",
        "prize_rank",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    def formatted_ticket_numbers(self, obj):
        return ", ".join(str(number) for number in obj.ticket_numbers)

    formatted_ticket_numbers.short_description = "추첨번호"
