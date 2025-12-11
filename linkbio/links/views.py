from django.db.models import F
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
    return render(
        request,
        "links/link_page.html",
        {
            "profile": profile,
            "links": links,
        },
    )


def track_link(request, slug: str, link_id: int):
    profile = get_object_or_404(Profile.objects.active(), slug=slug)
    link = get_object_or_404(Link, id=link_id, profile=profile)
    Link.objects.filter(id=link.id).update(click_count=F("click_count") + 1)
    return redirect(link.url)
