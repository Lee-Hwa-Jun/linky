from datetime import timedelta

from django.core.cache import cache
from django.db.models import F
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Link, Profile

import random


def landing(request, slug=None):
    queryset = Profile.objects.active().prefetch_related("links")
    if slug:
        profile = get_object_or_404(queryset, slug=slug)
    else:
        profile = queryset.first()
        if not profile:
            raise Http404("No active profile configured")

    links_qs = profile.links.all()
    marquee_texts = [profile.headline or "오늘도 멋진 하루 보내세요."] * 3

    search_query = (request.GET.get("q") or "").strip()
    active_hashtag = (request.GET.get("hashtag") or "").lstrip("#").strip()

    available_hashtags = sorted(
        {
            hashtag
            for link in links_qs
            for hashtag in link.hashtags_list
        }
    )

    if search_query:
        links_qs = links_qs.filter(label__icontains=search_query)
    if active_hashtag:
        links_qs = links_qs.filter(hashtags__icontains=active_hashtag)

    links = list(links_qs)
    return render(
        request,
        "links/link_page.html",
        {
            "profile": profile,
            "links": links,
            "marquee_texts": marquee_texts,
            "available_hashtags": available_hashtags,
            "active_hashtag": active_hashtag,
            "search_query": search_query,
        },
    )


def track_link(request, slug: str, link_id: int):
    profile = get_object_or_404(Profile.objects.active(), slug=slug)
    link = get_object_or_404(Link, id=link_id, profile=profile)
    Link.objects.filter(id=link.id).update(click_count=F("click_count") + 1)
    return redirect(link.url)


def profile_links(request, slug: str):
    profile = get_object_or_404(Profile.objects.active(), slug=slug)
    links = random.choice(list(profile.links.values_list("url", flat=True)))
    return JsonResponse({"links": links})


def lucky(request):
    ad_profile = Profile.objects.active().prefetch_related("links").filter(slug="moonis").first()
    ad_link = ad_profile.links.first() if ad_profile else None
    return render(
        request,
        "links/lucky.html",
        {
            "ad_profile": ad_profile,
            "ad_link": ad_link,
        },
    )


FORTUNES = [
    "오늘의 선택이 내일의 즐거움을 만듭니다.",
    "좋은 대답은 천천히, 좋은 행운은 갑자기 찾아와요.",
    "마음이 가는 길에 작은 선물을 발견하게 될 거예요.",
]


def _get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _fortune_cache_key(ip_address: str, date) -> str:
    return f"lucky:fortune:{ip_address}:{date.isoformat()}"


def _seconds_until_midnight() -> int:
    now = timezone.localtime()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((tomorrow - now).total_seconds()), 0)


def fortune_status(request):
    ip_address = _get_client_ip(request)
    today = timezone.localdate()
    cache_key = _fortune_cache_key(ip_address, today)
    cached = cache.get(cache_key)
    action = request.GET.get("action")

    if action == "reset":
        cache.delete(cache_key)
        return JsonResponse(
            {
                "status": "available",
                "message": "포춘쿠키를 다시 뽑을 수 있어요!",
            }
        )

    if cached is not None:
        index = cached.get("index", 0)
        fortune = FORTUNES[index % len(FORTUNES)]
        return JsonResponse(
            {
                "status": "already_drawn",
                "index": index,
                "fortune": fortune,
                "message": "이미 오늘의 포춘쿠키를 뽑았어요. 내일 다시 와주세요!",
            }
        )

    if action == "draw":
        index = random.randrange(len(FORTUNES))
        cache.set(cache_key, {"index": index}, timeout=_seconds_until_midnight())
        return JsonResponse(
            {
                "status": "drawn",
                "index": index,
                "fortune": FORTUNES[index],
            }
        )

    return JsonResponse({"status": "available"})
