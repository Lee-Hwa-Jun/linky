from urllib.parse import urlparse

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .lotto import (
    calculate_draw_round,
    draw_date_to_code,
    evaluate_ticket,
    normalize_lotto_numbers,
)


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
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    thread_url = models.URLField(blank=True)
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
    hashtags = models.CharField(max_length=255, blank=True, help_text="Comma-separated hashtags (without #)")
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

    @property
    def hashtags_list(self) -> list[str]:  # pragma: no cover - deterministic parsing
        return [tag.strip() for tag in self.hashtags.split(",") if tag.strip()]


class LottoDrawResult(models.Model):
    draw_round = models.PositiveIntegerField("추첨회차", unique=True)
    draw_date = models.DateField("추첨일자", unique=True)
    draw_date_code = models.CharField("추첨일자(yyyymmdd)", max_length=8, unique=True)
    winning_numbers = models.JSONField("당첨번호", default=list)
    bonus_number = models.PositiveSmallIntegerField("보너스 번호", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-draw_date", "-draw_round"]
        verbose_name = "로또 실제 추첨 결과"
        verbose_name_plural = "로또 실제 추첨 결과"

    def __str__(self) -> str:
        return f"{self.draw_round}회 ({self.draw_date_code})"

    def clean(self):
        self.winning_numbers = normalize_lotto_numbers(self.winning_numbers)
        self.draw_date_code = draw_date_to_code(self.draw_date)

        expected_round = calculate_draw_round(self.draw_date)
        if self.draw_round != expected_round:
            raise ValidationError(
                {"draw_round": f"{self.draw_date_code} 추첨일의 예상 회차는 {expected_round}회입니다."}
            )

        if self.bonus_number is not None:
            if self.bonus_number < 1 or self.bonus_number > 45:
                raise ValidationError({"bonus_number": "보너스 번호는 1부터 45 사이여야 합니다."})
            if self.bonus_number in self.winning_numbers:
                raise ValidationError({"bonus_number": "보너스 번호는 당첨번호와 중복될 수 없습니다."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        LottoTicket.recalculate_for_result(self)


class LottoTicket(models.Model):
    PRIZE_RANK_CHOICES = [
        (0, "낙첨"),
        (1, "1등"),
        (2, "2등"),
        (3, "3등"),
        (4, "4등"),
        (5, "5등"),
    ]

    session_key = models.CharField("세션 키", max_length=40, db_index=True)
    client_ip = models.GenericIPAddressField("IP", blank=True, null=True)
    user_agent = models.CharField("User-Agent", max_length=255, blank=True)
    ticket_numbers = models.JSONField("추첨번호", default=list)
    draw_date = models.DateField("추첨일자", db_index=True)
    draw_date_code = models.CharField("추첨일자(yyyymmdd)", max_length=8, db_index=True)
    draw_round = models.PositiveIntegerField("추첨회차", db_index=True)
    draw_result = models.ForeignKey(
        LottoDrawResult,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
        verbose_name="실제 추첨 결과",
    )
    matched_numbers = models.JSONField("일치 번호", default=list, blank=True)
    matched_count = models.PositiveSmallIntegerField("일치 개수", default=0)
    matched_bonus = models.BooleanField("보너스 번호 일치", default=False)
    prize_rank = models.PositiveSmallIntegerField("당첨 등수", choices=PRIZE_RANK_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "로또 티켓"
        verbose_name_plural = "로또 티켓"

    def __str__(self) -> str:
        return f"Ticket #{self.pk or 'new'} - {self.draw_round}회"

    def clean(self):
        self.ticket_numbers = normalize_lotto_numbers(self.ticket_numbers)
        self.draw_date_code = draw_date_to_code(self.draw_date)
        expected_round = calculate_draw_round(self.draw_date)
        if self.draw_round != expected_round:
            raise ValidationError(
                {"draw_round": f"{self.draw_date_code} 추첨일의 예상 회차는 {expected_round}회입니다."}
            )

    def apply_result(self, draw_result: LottoDrawResult | None):
        if not draw_result:
            self.draw_result = None
            self.matched_numbers = []
            self.matched_count = 0
            self.matched_bonus = False
            self.prize_rank = None
            return

        evaluation = evaluate_ticket(
            ticket_numbers=self.ticket_numbers,
            winning_numbers=draw_result.winning_numbers,
            bonus_number=draw_result.bonus_number,
        )
        self.draw_result = draw_result
        self.ticket_numbers = evaluation["ticket_numbers"]
        self.matched_numbers = evaluation["matched_numbers"]
        self.matched_count = evaluation["match_count"]
        self.matched_bonus = evaluation["bonus_match"]
        self.prize_rank = evaluation["prize_rank"]

    def save(self, *args, **kwargs):
        self.full_clean()
        draw_result = LottoDrawResult.objects.filter(
            draw_round=self.draw_round,
            draw_date=self.draw_date,
        ).first()
        self.apply_result(draw_result)
        super().save(*args, **kwargs)

    @classmethod
    def recalculate_for_result(cls, draw_result: LottoDrawResult):
        tickets = cls.objects.filter(draw_round=draw_result.draw_round, draw_date=draw_result.draw_date)
        for ticket in tickets:
            ticket.apply_result(draw_result)
            models.Model.save(
                ticket,
                update_fields=[
                    "draw_result",
                    "ticket_numbers",
                    "matched_numbers",
                    "matched_count",
                    "matched_bonus",
                    "prize_rank",
                    "updated_at",
                ]
            )
