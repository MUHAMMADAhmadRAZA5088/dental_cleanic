from django.db import models


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("booked", "Booked"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
        ("completed", "Completed"),
    ]

    LOCATION_CHOICES = [
        ("Jackson Heights", "Jackson Heights - 8202 Roosevelt Ave"),
        ("Woodside", "Woodside - 39-72 61st St"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100, choices=LOCATION_CHOICES, default="Jackson Heights")
    service = models.CharField(max_length=150)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="booked")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return f"{self.name} - {self.date} {self.time} ({self.status})"
