from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Reminder


def check_due_reminders():
    now = timezone.now()
    reminders = Reminder.objects.filter(remind_at__lte=now, is_sent=False)

    channel_layer = get_channel_layer()

    for reminder in reminders:
        group_name = f"user_{reminder.user.id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_reminder",
                "task": reminder.task,
            }
        )

        reminder.is_sent = True
        reminder.save()
