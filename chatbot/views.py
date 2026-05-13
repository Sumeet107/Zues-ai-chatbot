from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import localtime
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from datetime import timedelta
import json

from .models import ChatSession, ChatMessage, Reminder, Meeting, UserBehavior, SmartSuggestion, Memory
from .bot_logic import chatbot_response, analyze_user_behavior


# ─── AUTH VIEWS ───────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect("chat")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("chat")
        error = "Invalid username or password."

    return render(request, "chatbot/login.html", {"error": error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("chat")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")

        if password != confirm:
            error = "Passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = "Username already taken."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect("chat")

    return render(request, "chatbot/register.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required(login_url="login")
def dashboard_view(request):
    now = timezone.now()
    user = request.user

    upcoming_meetings = Meeting.objects.filter(
        user=user, status="upcoming", meeting_at__gte=now
    ).order_by("meeting_at")[:5]

    today_meetings = Meeting.objects.filter(
        user=user, status="upcoming",
        meeting_at__date=now.date()
    )

    pending_reminders = Reminder.objects.filter(
        user=user, is_sent=False, remind_at__gte=now
    ).order_by("remind_at")[:5]

    total_meetings = Meeting.objects.filter(user=user).count()
    completed = Meeting.objects.filter(user=user, status="completed").count()
    cancelled = Meeting.objects.filter(user=user, status="cancelled").count()

    suggestions = SmartSuggestion.objects.filter(user=user, is_dismissed=False)[:3]

    behavior, _ = UserBehavior.objects.get_or_create(user=user)

    return render(request, "chatbot/dashboard.html", {
        "upcoming_meetings": upcoming_meetings,
        "today_meetings": today_meetings,
        "pending_reminders": pending_reminders,
        "total_meetings": total_meetings,
        "completed": completed,
        "cancelled": cancelled,
        "suggestions": suggestions,
        "behavior": behavior,
        "now": now,
    })


# ─── CHAT / AI ASSISTANT ──────────────────────────────────────────────────────

@login_required(login_url="login")
def chat_view(request):
    user = request.user

    if request.method == "GET":
        session = ChatSession.objects.create(user=user)
        request.session["chat_session_id"] = session.id

    session_id = request.session.get("chat_session_id")
    try:
        session = ChatSession.objects.get(id=session_id, user=user)
    except ChatSession.DoesNotExist:
        session = ChatSession.objects.create(user=user)
        request.session["chat_session_id"] = session.id

    if request.method == "POST":
        user_message = request.POST.get("message", "").strip()
        if not user_message:
            return redirect("chat")

        ChatMessage.objects.create(session=session, sender="user", message=user_message)
        result = chatbot_response(user_message, user=user)

        # Handle REMINDER
        if result.get("type") == "reminder":
            if not result.get("task"):
                bot_reply = "📌 What should I remind you about?"
            elif not result.get("remind_at"):
                bot_reply = "⏰ When should I remind you?"
            else:
                reminder = Reminder.objects.create(
                    user=user,
                    task=result["task"],
                    remind_at=result["remind_at"],
                    is_ai_suggested=True
                )
                time_str = localtime(reminder.remind_at).strftime("%d %b %Y, %I:%M %p")
                bot_reply = f"✅ **Reminder Synchronized**: {reminder.task} at {time_str}"
                if result.get("ai_note"):
                    bot_reply += f"\n\n_{result['ai_note']}_"

        # Handle MEETING
        elif result.get("type") == "meeting":
            meeting = Meeting.objects.create(
                user=user,
                title=result.get("title", "Meeting"),
                description=result.get("description", ""),
                participants=result.get("participants", ""),
                meeting_at=result.get("meeting_at"),
                priority=result.get("priority", "medium"),
                location=result.get("location", ""),
            )
            # Auto-set a reminder 15 mins before
            remind_at = meeting.meeting_at - timedelta(minutes=15)
            if remind_at > timezone.now():
                Reminder.objects.create(
                    user=user,
                    meeting=meeting,
                    task=f"Meeting: {meeting.title}",
                    remind_at=remind_at,
                    is_ai_suggested=True
                )
            time_str = localtime(meeting.meeting_at).strftime("%d %b %Y, %I:%M %p")
            bot_reply = f"📅 Meeting **{meeting.title}** scheduled for {time_str}. A reminder has been set 15 minutes before!"

        # Handle PLAN or CHAT
        else:
            bot_reply = result.get("response", "I'm here to help with your meetings!")

        ChatMessage.objects.create(session=session, sender="bot", message=bot_reply)

    messages = ChatMessage.objects.filter(session=session).order_by("timestamp")
    
    # Fetch additional data for ZEUS UI panels
    upcoming_reminders = Reminder.objects.filter(user=user, is_sent=False, remind_at__gte=timezone.now()).order_by('remind_at')[:5]
    recent_memories = Memory.objects.filter(user=user).order_by('-updated_at')[:5]
    behavior = UserBehavior.objects.filter(user=user).first()
    
    return render(request, "chatbot/chat.html", {
        "messages": messages, 
        "session": session,
        "upcoming_reminders": upcoming_reminders,
        "recent_memories": recent_memories,
        "behavior": behavior
    })


# ─── MEETINGS CRUD ────────────────────────────────────────────────────────────

@login_required(login_url="login")
def meetings_view(request):
    user = request.user
    now = timezone.now()

    filter_status = request.GET.get("status", "all")
    filter_priority = request.GET.get("priority", "all")

    meetings = Meeting.objects.filter(user=user)
    if filter_status != "all":
        meetings = meetings.filter(status=filter_status)
    if filter_priority != "all":
        meetings = meetings.filter(priority=filter_priority)

    meetings = meetings.order_by("meeting_at")

    return render(request, "chatbot/meetings.html", {
        "meetings": meetings,
        "filter_status": filter_status,
        "filter_priority": filter_priority,
        "now": now,
    })


@login_required(login_url="login")
def create_meeting_view(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        participants = request.POST.get("participants", "").strip()
        meeting_at_str = request.POST.get("meeting_at", "")
        location = request.POST.get("location", "").strip()
        priority = request.POST.get("priority", "medium")
        notes = request.POST.get("notes", "").strip()
        reminder_lead = int(request.POST.get("reminder_lead", 15))

        from django.utils.dateparse import parse_datetime
        meeting_at = parse_datetime(meeting_at_str)

        if title and meeting_at:
            meeting = Meeting.objects.create(
                user=request.user,
                title=title,
                description=description,
                participants=participants,
                meeting_at=timezone.make_aware(meeting_at) if timezone.is_naive(meeting_at) else meeting_at,
                location=location,
                priority=priority,
                notes=notes,
            )
            # Set reminder
            remind_at = meeting.meeting_at - timedelta(minutes=reminder_lead)
            if remind_at > timezone.now():
                Reminder.objects.create(
                    user=request.user,
                    meeting=meeting,
                    task=f"Meeting: {meeting.title}",
                    remind_at=remind_at,
                )
            return redirect("meetings")

    return render(request, "chatbot/create_meeting.html")


@login_required(login_url="login")
def edit_meeting_view(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk, user=request.user)

    if request.method == "POST":
        meeting.title = request.POST.get("title", meeting.title).strip()
        meeting.description = request.POST.get("description", meeting.description).strip()
        meeting.participants = request.POST.get("participants", meeting.participants).strip()
        meeting.location = request.POST.get("location", meeting.location).strip()
        meeting.priority = request.POST.get("priority", meeting.priority)
        meeting.status = request.POST.get("status", meeting.status)
        meeting.notes = request.POST.get("notes", meeting.notes).strip()

        meeting_at_str = request.POST.get("meeting_at", "")
        from django.utils.dateparse import parse_datetime
        meeting_at = parse_datetime(meeting_at_str)
        if meeting_at:
            meeting.meeting_at = timezone.make_aware(meeting_at) if timezone.is_naive(meeting_at) else meeting_at

        meeting.save()
        return redirect("meetings")

    return render(request, "chatbot/edit_meeting.html", {"meeting": meeting})


@login_required(login_url="login")
def delete_meeting_view(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk, user=request.user)
    meeting.delete()
    return redirect("meetings")


@login_required(login_url="login")
def meeting_detail_view(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk, user=request.user)
    reminders = Reminder.objects.filter(meeting=meeting)
    return render(request, "chatbot/meeting_detail.html", {
        "meeting": meeting,
        "reminders": reminders,
    })


# ─── REMINDERS ────────────────────────────────────────────────────────────────

@login_required(login_url="login")
def reminders_view(request):
    user = request.user
    now = timezone.now()

    upcoming = Reminder.objects.filter(user=user, remind_at__gte=now, is_sent=False).order_by("remind_at")
    past = Reminder.objects.filter(
        Q(is_sent=True) | Q(remind_at__lt=now)
    ).filter(user=user).order_by("-remind_at")[:20]

    return render(request, "chatbot/reminders.html", {
        "upcoming": upcoming,
        "past": past,
        "now": now,
    })


@login_required(login_url="login")
def delete_reminder_view(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.delete()
    return redirect("reminders")


# ─── AI ANALYSIS ──────────────────────────────────────────────────────────────

@login_required(login_url="login")
def ai_analysis_view(request):
    user = request.user
    behavior, _ = UserBehavior.objects.get_or_create(user=user)
    suggestions = SmartSuggestion.objects.filter(user=user, is_dismissed=False)

    analysis_result = None
    if request.method == "POST":
        result = analyze_user_behavior(user)
        # Save as suggestion
        if result.get("type") in ("analysis", "chat"):
            body = result.get("summary") or result.get("response", "")
            sugg_list = result.get("suggestions", [])
            SmartSuggestion.objects.create(
                user=user,
                suggestion_type="habit",
                title="AI Behavior Analysis",
                body=body + ("\n\n💡 " + "\n💡 ".join(sugg_list) if sugg_list else "")
            )
        analysis_result = result
        # Refresh
        behavior.refresh_from_db()
        suggestions = SmartSuggestion.objects.filter(user=user, is_dismissed=False)

    return render(request, "chatbot/ai_analysis.html", {
        "behavior": behavior,
        "suggestions": suggestions,
        "analysis_result": analysis_result,
    })


@login_required(login_url="login")
def dismiss_suggestion_view(request, pk):
    suggestion = get_object_or_404(SmartSuggestion, pk=pk, user=request.user)
    suggestion.is_dismissed = True
    suggestion.save()
    return redirect("ai_analysis")


# ─── API: CHECK DUE REMINDERS (polling) ───────────────────────────────────────

def check_reminders(request):
    if not request.user.is_authenticated:
        return JsonResponse({"reminders": []})

    now = timezone.now()
    due = Reminder.objects.filter(user=request.user, remind_at__lte=now, is_sent=False)
    data = []
    for r in due:
        data.append({"id": r.id, "task": r.task})
        r.is_sent = True
        r.save()

    return JsonResponse({"reminders": data})


# ─── MEMORY MANAGEMENT ────────────────────────────────────────────────────────

@login_required(login_url="login")
def memory_view(request):
    user = request.user
    memories = Memory.objects.filter(user=user).order_by('category', '-updated_at')
    
    categories = [c[0] for c in Memory.CATEGORY_CHOICES]
    stats = {cat: memories.filter(category=cat).count() for cat in categories}

    return render(request, "chatbot/memory.html", {
        "memories": memories,
        "stats": stats,
    })


@login_required(login_url="login")
@require_POST
def delete_memory_view(request, pk):
    memory = get_object_or_404(Memory, pk=pk, user=request.user)
    memory.delete()
    return redirect("memory_list")