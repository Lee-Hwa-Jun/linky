from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
import os

admin_url = os.getenv('ADMIN_URL', 'admin/')

urlpatterns = [
    path(admin_url, admin.site.urls),
    path('extentions/', include('extentions.urls')),
    path('', include('linkbio.links.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
