from django.db.models import F, Sum
from django.http import Http404
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

    links = profile.links.all()
    total_clicks = links.aggregate(total=Sum("click_count")).get("total") or 0
    marquee_texts = [profile.headline or "오늘도 멋진 하루 보내세요."] * 3
    return render(
        request,
        "links/link_page.html",
        {
            "profile": profile,
            "links": links,
            "total_clicks": total_clicks,
            "marquee_texts": marquee_texts,
        },
    )


def track_link(request, slug: str, link_id: int):
    profile = get_object_or_404(Profile.objects.active(), slug=slug)
    link = get_object_or_404(Link, id=link_id, profile=profile)
    Link.objects.filter(id=link.id).update(click_count=F("click_count") + 1)
    return redirect(link.url)
