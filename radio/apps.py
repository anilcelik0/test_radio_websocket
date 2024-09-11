from django.apps import AppConfig
import threading
from .radio_server import start_radio_server


class RadioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'radio'

    def ready(self):
        threading.Thread(target=start_radio_server, daemon=True).start()