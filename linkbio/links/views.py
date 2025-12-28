from django.db.models import F
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Link, Profile


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
    links = list(profile.links.values_list("url", flat=True))
    return JsonResponse({"links": links})
