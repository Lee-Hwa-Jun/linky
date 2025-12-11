from django.test import Client, TestCase
from django.urls import reverse

from .models import Link, Profile


class LandingViewTests(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(
            name="코코 데코",
            slug="coco",
            headline="감성 인테리어 소품",
            bio="아기자기한 홈데코를 만나보세요",
            avatar_url="https://placehold.co/128x128",
            background_url="https://placehold.co/800x600",
        )
        Link.objects.create(
            profile=self.profile,
            label="인스타그램", url="https://instagram.com", icon="\uf16d", is_primary=True
        )
        self.client = Client()

    def test_root_uses_first_profile(self):
        response = self.client.get(reverse("links:landing"))
        self.assertContains(response, self.profile.name)
        self.assertContains(response, "인스타그램")

    def test_profile_slug_page(self):
        response = self.client.get(reverse("links:profile", args=[self.profile.slug]))
        self.assertContains(response, self.profile.bio)

    def test_missing_profile_returns_404(self):
        Profile.objects.all().delete()
        response = self.client.get(reverse("links:landing"))
        self.assertEqual(response.status_code, 404)
