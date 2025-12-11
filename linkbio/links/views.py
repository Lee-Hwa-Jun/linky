from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Profile


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
