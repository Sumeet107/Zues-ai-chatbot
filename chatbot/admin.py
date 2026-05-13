from django.contrib import admin
from .models import ChatSession, ChatMessage, Meeting, Reminder, UserBehavior, SmartSuggestion


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'meeting_at', 'priority', 'status']
    list_filter = ['status', 'priority', 'user']
    search_fields = ['title', 'description', 'participants']
    ordering = ['meeting_at']


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'remind_at', 'is_sent', 'is_ai_suggested']
    list_filter = ['is_sent', 'is_ai_suggested', 'user']
    ordering = ['remind_at']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'started_at']
    ordering = ['-started_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'sender', 'message', 'timestamp']
    list_filter = ['sender']


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_meetings', 'completed_meetings', 'most_productive_hour', 'last_analyzed']


@admin.register(SmartSuggestion)
class SmartSuggestionAdmin(admin.ModelAdmin):
    list_display = ['user', 'suggestion_type', 'title', 'is_dismissed', 'created_at']
    list_filter = ['suggestion_type', 'is_dismissed']
