from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("taxis.urls")),
]

# Explicit static/media routes — required under Passenger, which strips
# SCRIPT_NAME in ways that break the default staticfiles app in some
# cPanel configs. Mirrors the pattern used across every PHYB project.
urlpatterns += [
    re_path(
        r"^static/(?P<path>.*)$",
        serve,
        {"document_root": settings.STATIC_ROOT},
    ),
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
