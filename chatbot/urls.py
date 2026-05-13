from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Chat / AI Assistant (PRIMARY LANDING)
    path("", views.chat_view, name="chat"),

    # Dashboard (SECONDARY)
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Meetings
    path("meetings/", views.meetings_view, name="meetings"),
    path("meetings/create/", views.create_meeting_view, name="create_meeting"),
    path("meetings/<int:pk>/", views.meeting_detail_view, name="meeting_detail"),
    path("meetings/<int:pk>/edit/", views.edit_meeting_view, name="edit_meeting"),
    path("meetings/<int:pk>/delete/", views.delete_meeting_view, name="delete_meeting"),

    # Reminders
    path("reminders/", views.reminders_view, name="reminders"),
    path("reminders/<int:pk>/delete/", views.delete_reminder_view, name="delete_reminder"),

    # AI Analysis
    path("analysis/", views.ai_analysis_view, name="ai_analysis"),
    path("analysis/dismiss/<int:pk>/", views.dismiss_suggestion_view, name="dismiss_suggestion"),

    # Memory
    path("memory/", views.memory_view, name="memory_list"),
    path("memory/<int:pk>/delete/", views.delete_memory_view, name="delete_memory"),

    # API
    path("api/check-reminders/", views.check_reminders, name="check_reminders"),
]
