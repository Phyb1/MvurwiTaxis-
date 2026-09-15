from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.static import serve

from taxis.sitemaps import DriverSitemap, StaticViewSitemap
from taxis.views import admin_leads_dashboard

sitemaps = {"drivers": DriverSitemap, "static": StaticViewSitemap}

urlpatterns = [
    # Registered before admin.site.urls so it isn't shadowed by the catch-all.
    path("admin/leads-dashboard/", admin_leads_dashboard, name="admin_leads_dashboard"),
    path("admin/", admin.site.urls),
    path("", include("taxis.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),

    # Password reset/change use Django's built-in views + our own dark-themed
    # templates in templates/registration/. Login/logout/signup stay on the
    # custom taxis: views since those carry driver-specific branding + logic.
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html",
    ), name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html",
    ), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html",
    ), name="password_reset_complete"),
    path("password-change/", auth_views.PasswordChangeView.as_view(
        template_name="registration/password_change_form.html",
    ), name="password_change"),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="registration/password_change_done.html",
    ), name="password_change_done"),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

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
