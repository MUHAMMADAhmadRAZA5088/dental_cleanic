from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "location", "service", "date", "time", "status")
    list_filter = ("status", "location", "date")
    search_fields = ("name", "phone")
