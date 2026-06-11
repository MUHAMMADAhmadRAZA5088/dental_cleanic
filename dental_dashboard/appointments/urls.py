from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("add/", views.add_appointment, name="add_appointment"),
    path("edit/<int:pk>/", views.edit_appointment, name="edit_appointment"),
    path("cancel/<int:pk>/", views.cancel_appointment_view, name="cancel_appointment"),
    path("delete/<int:pk>/", views.delete_appointment_view, name="delete_appointment"),
    path("webhook/vapi/", views.vapi_webhook, name="vapi_webhook"),
]
