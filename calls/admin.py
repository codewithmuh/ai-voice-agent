from django.contrib import admin
from .models import CallLog


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ("caller_phone", "appointment_booked", "duration_seconds", "created_at")
    list_filter = ("appointment_booked", "created_at")
    search_fields = ("caller_phone", "call_summary")
    readonly_fields = ("created_at",)
