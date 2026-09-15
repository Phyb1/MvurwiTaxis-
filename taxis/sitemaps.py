from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from taxis.models import Driver


class DriverSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Driver.objects.filter(is_active_listing=True)

    def location(self, driver):
        return reverse("taxis:driver_profile", args=[driver.slug])

    def lastmod(self, driver):
        return driver.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return ["taxis:home", "taxis:fares", "taxis:faqs", "taxis:request_taxi", "taxis:driver_signup"]

    def location(self, item):
        return reverse(item)
