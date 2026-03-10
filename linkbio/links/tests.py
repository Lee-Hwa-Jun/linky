import shutil
import tempfile
import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .lotto import calculate_draw_round, determine_draw_date, evaluate_ticket
from .models import Link, LottoDrawResult, LottoTicket, Profile


@override_settings(MEDIA_ROOT=Path(tempfile.gettempdir()) / "linky_tests_media")
class LandingViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = Path(tempfile.gettempdir()) / "linky_tests_media"
        cls.media_root.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        avatar_file = SimpleUploadedFile(
            "avatar.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;",
            content_type="image/gif",
        )
        self.profile = Profile.objects.create(
            name="코코 데코",
            slug="coco",
            headline="감성 인테리어 소품",
            bio="아기자기한 홈데코를 만나보세요",
            avatar=avatar_file,
            background_url="https://placehold.co/800x600",
            show_total_clicks=True,
        )
        Link.objects.create(
            profile=self.profile,
            label="인스타그램",
            url="https://instagram.com",
            icon="\uf16d",
            is_primary=True,
            click_count=5,
        )
        self.client = Client()

    def test_root_uses_first_profile(self):
        response = self.client.get(reverse("links:landing"))
        self.assertContains(response, self.profile.name)
        self.assertContains(response, "인스타그램")

    def test_profile_slug_page(self):
        response = self.client.get(reverse("links:profile", args=[self.profile.slug]))
        self.assertContains(response, self.profile.bio)
        self.assertContains(response, "총 5 클릭")
        self.assertContains(response, "/media/avatars/")

    def test_profile_page_hides_total_clicks_when_disabled(self):
        self.profile.show_total_clicks = False
        self.profile.save()
        response = self.client.get(reverse("links:profile", args=[self.profile.slug]))
        self.assertNotContains(response, "총 5 클릭")

    def test_icon_image_renders_img_tag(self):
        Link.objects.create(
            profile=self.profile,
            label="블로그",
            url="https://blog.example.com",
            icon="https://example.com/icon.png",
        )
        response = self.client.get(reverse("links:profile", args=[self.profile.slug]))
        self.assertContains(response, "hero__icon-img")

    def test_uploaded_icon_image_has_priority_over_text_icon(self):
        icon_file = SimpleUploadedFile(
            "icon.gif",
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;",
            content_type="image/gif",
        )
        Link.objects.create(
            profile=self.profile,
            label="홈페이지",
            url="https://home.example.com",
            icon="🙂",
            icon_image=icon_file,
        )
        response = self.client.get(reverse("links:profile", args=[self.profile.slug]))
        self.assertContains(response, "link_icons/")
        self.assertContains(response, "hero__icon-img")

    def test_missing_profile_returns_404(self):
        Profile.objects.all().delete()
        response = self.client.get(reverse("links:landing"))
        self.assertEqual(response.status_code, 404)


class LottoLogicTests(TestCase):
    def test_determine_draw_date_moves_to_next_week_after_cutoff(self):
        seoul = ZoneInfo("Asia/Seoul")

        saturday_before_cutoff = datetime(2026, 3, 14, 20, 59, tzinfo=seoul)
        saturday_after_cutoff = datetime(2026, 3, 14, 21, 0, tzinfo=seoul)
        sunday = datetime(2026, 3, 15, 10, 0, tzinfo=seoul)

        self.assertEqual(determine_draw_date(saturday_before_cutoff), date(2026, 3, 14))
        self.assertEqual(determine_draw_date(saturday_after_cutoff), date(2026, 3, 21))
        self.assertEqual(determine_draw_date(sunday), date(2026, 3, 21))

    def test_calculate_draw_round_uses_1215_as_anchor(self):
        self.assertEqual(calculate_draw_round(date(2026, 3, 14)), 1215)
        self.assertEqual(calculate_draw_round(date(2026, 3, 21)), 1216)

    def test_evaluate_ticket_returns_second_prize_when_bonus_matches(self):
        evaluation = evaluate_ticket([1, 2, 3, 4, 5, 7], [1, 2, 3, 4, 5, 6], bonus_number=7)
        self.assertEqual(evaluation["prize_rank"], 2)
        self.assertEqual(evaluation["matched_numbers"], [1, 2, 3, 4, 5])


class LottoViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.moonis = Profile.objects.create(name="Moonis", slug="moonis", is_active=True)
        Link.objects.create(profile=self.moonis, label="쿠팡", url="https://example.com/coupang")

    def test_submit_stores_ticket_with_expected_draw_metadata(self):
        seoul = ZoneInfo("Asia/Seoul")
        draw_time = datetime(2026, 3, 14, 21, 5, tzinfo=seoul)

        with patch("linkbio.links.views.timezone.now", return_value=draw_time):
            response = self.client.post(
                reverse("links:lotto_submit"),
                data=json.dumps({"numbers": [1, 2, 3, 4, 5, 6]}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ticket = LottoTicket.objects.get(id=payload["ticket_id"])

        self.assertEqual(ticket.draw_date_code, "20260321")
        self.assertEqual(ticket.draw_round, 1216)
        self.assertNotIn("lotto_auto_link_opened_on", self.client.session)

    def test_lotto_ad_open_marks_today_and_redirects(self):
        with patch("linkbio.links.views.timezone.localdate", return_value=date(2026, 3, 10)):
            response = self.client.get(reverse("links:lotto_ad_open"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://example.com/coupang")
        self.assertEqual(self.client.session["lotto_auto_link_opened_on"], "20260310")

    def test_lotto_page_resets_auto_open_flag_next_day(self):
        session = self.client.session
        session["lotto_auto_link_opened_on"] = "20260309"
        session.save()

        with patch("linkbio.links.views.timezone.localdate", return_value=date(2026, 3, 10)):
            response = self.client.get(reverse("links:lotto"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-auto-link-consumed="false"')

    def test_result_save_recalculates_matching_tickets(self):
        ticket = LottoTicket.objects.create(
            session_key="session-1",
            ticket_numbers=[1, 2, 3, 4, 5, 7],
            draw_date=date(2026, 3, 14),
            draw_date_code="20260314",
            draw_round=1215,
        )

        result = LottoDrawResult.objects.create(
            draw_round=1215,
            draw_date=date(2026, 3, 14),
            draw_date_code="20260314",
            winning_numbers=[1, 2, 3, 4, 5, 6],
            bonus_number=7,
        )

        ticket.refresh_from_db()

        self.assertEqual(ticket.draw_result, result)
        self.assertEqual(ticket.prize_rank, 2)
        self.assertEqual(ticket.matched_count, 5)
        self.assertTrue(ticket.matched_bonus)

    def test_lotto_page_renders_selected_result_winners(self):
        result = LottoDrawResult.objects.create(
            draw_round=1215,
            draw_date=date(2026, 3, 14),
            draw_date_code="20260314",
            winning_numbers=[1, 2, 3, 4, 5, 6],
            bonus_number=7,
        )
        LottoTicket.objects.create(
            session_key="session-1",
            ticket_numbers=[1, 2, 3, 4, 5, 6],
            draw_date=date(2026, 3, 14),
            draw_date_code="20260314",
            draw_round=1215,
        )

        response = self.client.get(reverse("links:lotto"), {"round": 1215})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "실제 추첨 결과")
        self.assertContains(response, f"{result.draw_round}회")
        self.assertContains(response, "1등")
