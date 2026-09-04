from django.contrib import admin, messages

from taxis.models import Driver, Fare, GoingToPost, Lead, Payment, Review


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
    list_display = ("kind", "pickup", "destination", "status", "unlocked_by", "created_at")
    list_filter = ("kind", "status")
    search_fields = ("passenger_name", "passenger_phone", "pickup", "destination")


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
