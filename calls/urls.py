from django.urls import path
from . import views

urlpatterns = [
    path("api/vapi/webhook/", views.vapi_webhook, name="vapi_webhook"),
]
