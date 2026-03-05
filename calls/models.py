from django.db import models


class CallLog(models.Model):
    caller_phone = models.CharField(max_length=20)
    call_summary = models.TextField(blank=True)
    appointment_booked = models.BooleanField(default=False)
    duration_seconds = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.caller_phone} — {'Booked' if self.appointment_booked else 'No booking'}"


class Appointment(models.Model):
    patient_name = models.CharField(max_length=100)
    patient_phone = models.CharField(max_length=20)
    appointment_type = models.CharField(
        max_length=20,
        choices=[
            ("new_patient", "New Patient"),
            ("returning", "Returning"),
            ("emergency", "Emergency"),
        ],
    )
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)
    google_event_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.patient_name} — {self.date} {self.time}"
