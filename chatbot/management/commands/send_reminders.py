from django.core.management.base import BaseCommand
from django.utils import timezone
from chatbot.models import Reminder

class Command(BaseCommand):
    help = "Send due reminders"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        reminders = Reminder.objects.filter(
            remind_at__lte=now,
            is_sent=False
        )

        for reminder in reminders:
            print(
                f"🔔 REMINDER for {reminder.user.username}: {reminder.task}"
            )
            reminder.is_sent = True
            reminder.save()
