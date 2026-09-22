from django.urls import path

from taxis import views

app_name = "taxis"

urlpatterns = [
    path("", views.home, name="home"),
    path("fares/", views.fares, name="fares"),
    path("d/<slug:slug>/", views.driver_profile, name="driver_profile"),
    path("d/<slug:slug>/message/", views.DirectRequestView.as_view(), name="direct_request"),
    path("d/<slug:slug>/whatsapp/", views.WhatsAppRedirectView.as_view(), name="whatsapp_redirect"),
    path("request/", views.request_taxi, name="request_taxi"),
    path("request/<uuid:token>/", views.LeadStatusView.as_view(), name="lead_status"),

    path("signup/", views.driver_signup, name="driver_signup"),
    path("login/", views.DriverLoginView.as_view(), name="driver_login"),
    path("logout/", views.driver_logout, name="driver_logout"),

    path("dashboard/", views.driver_dashboard, name="driver_dashboard"),
    path("dashboard/toggle-online/", views.toggle_online, name="toggle_online"),
    path("dashboard/edit-profile/", views.edit_profile, name="edit_profile"),
    path("dashboard/lead/<int:lead_id>/unlock/", views.UnlockLeadView.as_view(), name="unlock_lead"),
    path("dashboard/lead/<int:lead_id>/decline/", views.DeclineLeadView.as_view(), name="decline_lead"),
    path("dashboard/tab/", views.TabView.as_view(), name="tab"),
    path("dashboard/go-pro/", views.go_pro, name="go_pro"),
    path("dashboard/going-to/new/", views.post_going_to, name="post_going_to"),

    path("faqs/", views.faqs, name="faqs"),
    path("push/subscribe/", views.push_subscribe, name="push_subscribe"),
    path("push/unsubscribe/", views.push_unsubscribe, name="push_unsubscribe"),
    path("service-worker.js", views.service_worker, name="service_worker"),
]
