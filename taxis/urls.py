from django.urls import path

from taxis import views

app_name = "taxis"

urlpatterns = [
    path("", views.home, name="home"),
    path("fares/", views.fares, name="fares"),
    path("d/<slug:slug>/", views.driver_profile, name="driver_profile"),
    path("request/", views.request_taxi, name="request_taxi"),
    path("request/<int:lead_id>/sent/", views.request_taxi_sent, name="request_taxi_sent"),

    path("signup/", views.driver_signup, name="driver_signup"),
    path("login/", views.DriverLoginView.as_view(), name="driver_login"),
    path("logout/", views.driver_logout, name="driver_logout"),

    path("dashboard/", views.driver_dashboard, name="driver_dashboard"),
    path("dashboard/toggle-online/", views.toggle_online, name="toggle_online"),
    path("dashboard/edit-profile/", views.edit_profile, name="edit_profile"),
    path("dashboard/lead/<int:lead_id>/unlock/", views.unlock_lead, name="unlock_lead"),
    path("dashboard/go-pro/", views.go_pro, name="go_pro"),
    path("dashboard/going-to/new/", views.post_going_to, name="post_going_to"),
    path("dashboard/lead/<int:lead_id>/claim/", views.claim_lead_pro, name="claim_lead_pro"),

    path("faqs/", views.faqs, name="faqs"),
]
