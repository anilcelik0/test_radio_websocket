from django.urls import path
from .views import index

urlpatterns = [
    path("radio_websocket", index, name="radio_websocket")
]
