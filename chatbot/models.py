from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat with {self.user.username} @ {self.started_at.strftime('%d %b %Y')}"


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10)  # user or bot
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"


class Meeting(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    participants = models.TextField(blank=True, help_text="Comma-separated participant names/emails")
    meeting_at = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='upcoming')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['meeting_at']

    def __str__(self):
        return f"{self.title} @ {self.meeting_at.strftime('%d %b %Y %I:%M %p')}"


class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    task = models.CharField(max_length=255)
    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    is_ai_suggested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['remind_at']

    def __str__(self):
        return f"{self.task} @ {self.remind_at.strftime('%d %b %Y %I:%M %p')}"


class UserBehavior(models.Model):
    """Tracks user patterns for AI-driven smart reminder suggestions."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Productivity patterns
    most_productive_hour = models.IntegerField(default=9)  # 0-23
    avg_meeting_duration_mins = models.IntegerField(default=60)
    preferred_reminder_lead_mins = models.IntegerField(default=15)  # How early user likes reminders
    total_meetings = models.IntegerField(default=0)
    completed_meetings = models.IntegerField(default=0)
    cancelled_meetings = models.IntegerField(default=0)

    # Behavioral tags (JSON string)
    behavior_tags = models.TextField(default="[]")

    # AI summary updated periodically
    ai_summary = models.TextField(blank=True)
    last_analyzed = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Behavior profile of {self.user.username}"


class SmartSuggestion(models.Model):
    """AI-generated proactive suggestions for the user."""
    SUGGESTION_TYPES = [
        ('reminder', 'Reminder Suggestion'),
        ('schedule', 'Schedule Optimization'),
        ('habit', 'Habit Insight'),
        ('meeting', 'Meeting Preparation'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    suggestion_type = models.CharField(max_length=20, choices=SUGGESTION_TYPES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.suggestion_type}] {self.title}"


class Memory(models.Model):
    """Persistent AI memory for storing user preferences, habits, and facts."""
    CATEGORY_CHOICES = [
        ('preference', 'Preference'),
        ('schedule', 'Schedule'),
        ('personal', 'Personal'),
        ('work', 'Work'),
        ('study', 'Study'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memories')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='personal')
    key = models.CharField(max_length=255)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Memories"
        unique_together = ('user', 'category', 'key')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} | {self.category}: {self.key}"
