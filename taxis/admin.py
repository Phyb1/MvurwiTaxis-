from django.contrib import admin, messages

from taxis.models import (
    FAQ, Driver, Fare, GoingToPost, Lead, Payment, PushSubscription, Review, TabEntry,
)

# Adds a "Leads & Payments Dashboard" link to the top of the admin index.
# Uses a differently-named template (custom_index.html) that itself extends
# "admin/index.html" — extending a template of the SAME name as the file
# it's defined in would recurse infinitely through the loader, since our
# project templates dir is searched before django.contrib.admin's.
admin.site.index_template = "admin/custom_index.html"
admin.site.site_header = "MvurwiTaxis Admin"
admin.site.site_title = "MvurwiTaxis"
admin.site.index_title = "Dashboard"


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "car_reg", "car_type", "is_verified", "is_pro", "is_online", "is_active_listing")
    list_filter = ("is_verified", "car_type", "is_active_listing")
    search_fields = ("full_name", "car_reg", "phone_number", "slug")
    actions = ["verify_drivers", "suspend_drivers"]
    readonly_fields = ("slug", "created_at", "updated_at")

    @admin.action(description="Mark selected drivers as Verified")
    def verify_drivers(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} driver(s) verified.", messages.SUCCESS)

    @admin.action(description="Suspend selected drivers (unlist)")
    def suspend_drivers(self, request, queryset):
        updated = queryset.update(is_active_listing=False)
        self.message_user(request, f"{updated} driver(s) suspended.", messages.WARNING)


@admin.register(Fare)
class FareAdmin(admin.ModelAdmin):
    list_display = ("origin", "destination", "price_usd", "order", "updated_at")
    list_editable = ("price_usd", "order")
    search_fields = ("destination",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "kind", "passenger_name", "pickup", "destination", "status",
        "target_driver", "unlocked_by", "created_at",
    )
    list_filter = ("kind", "status")
    search_fields = ("passenger_name", "passenger_phone", "pickup", "destination")
    readonly_fields = ("token", "created_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("driver", "purpose", "method", "status", "amount_usd", "created_at")
    list_filter = ("purpose", "method", "status")
    search_fields = ("driver__full_name", "ecocash_reference")
    actions = ["confirm_payments"]

    @admin.action(description="Confirm selected payments (applies effect)")
    def confirm_payments(self, request, queryset):
        count = 0
        for payment in queryset.exclude(status=Payment.Status.CONFIRMED):
            payment.confirm()
            count += 1
        self.message_user(request, f"{count} payment(s) confirmed and applied.", messages.SUCCESS)


@admin.register(GoingToPost)
class GoingToPostAdmin(admin.ModelAdmin):
    list_display = ("driver", "destination", "seats_available", "price_usd", "expires_at")
    list_filter = ("is_pinned_paid",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("driver", "rating", "passenger_name", "created_at")
    list_filter = ("rating",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "audience", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("audience", "is_published")


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("driver", "created_at")
    search_fields = ("driver__full_name",)


@admin.register(TabEntry)
class TabEntryAdmin(admin.ModelAdmin):
    list_display = ("driver", "amount_usd", "lead", "created_at", "settled_by")
    list_filter = (("settled_by", admin.EmptyFieldListFilter),)
    search_fields = ("driver__full_name", "driver__phone_number")
