import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Link, Profile


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
