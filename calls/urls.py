from django.urls import path
from . import views

urlpatterns = [
    path("api/vapi/webhook/", views.vapi_webhook, name="vapi_webhook"),
    path("api/vapi/chat/completions/", views.chat_completions, name="chat_completions"),
    path("api/vapi/chat/completions", views.chat_completions, name="chat_completions_no_slash"),
]
