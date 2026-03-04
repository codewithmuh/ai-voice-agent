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
