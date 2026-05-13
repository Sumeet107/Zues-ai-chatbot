from django.apps import AppConfig
import threading
import time


class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot"

    def ready(self):
        from .scheduler import check_due_reminders

        def run_scheduler():
            while True:
                try:
                    check_due_reminders()
                except Exception:
                    pass  # DB may not be ready on first boot
                time.sleep(10)

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
