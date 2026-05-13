import requests
import json
import logging
import re
from datetime import datetime, timedelta
from django.utils import timezone
from .memory_utils import get_memory_context, extract_memories_from_text

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZEUS_AI")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT: THE BRAIN OF ZEUS
# ──────────────────────────────────────────────────────────────────────────────

ZEUS_SYSTEM_PROMPT = """
You are ZEUS AI — a highly advanced, autonomous AI Operating System and Productivity Agent.
Your mission: Think. Plan. Execute.

CORE DIRECTIVES:
1. Be proactive, intelligent, and agentic. You don't just chat; you solve problems.
2. Act as the user's executive assistant, managing their schedule and focus.
3. Use a futuristic, sophisticated, yet concise tone.
4. Utilize user memories and schedule data to provide hyper-personalized assistance.

CAPABILITIES:
- Setting reminders for tasks and follow-ups.
- Scheduling and analyzing meetings.
- Strategic planning and habit optimization.
- Context-aware intelligence using long-term memory.

OUTPUT FORMAT (STRICT JSON):
You must ALWAYS respond in valid JSON format. Do not include any text before or after the JSON.

[FORMATS]

1. REMINDER (When user wants to be notified of something):
{{
  "type": "reminder",
  "task": "Call the manager regarding the report",
  "time_minutes": 15,
  "priority": "high",
  "ai_note": "A futuristic proactive note about why this matters."
}}

2. MEETING (When scheduling a formal event):
{{
  "type": "meeting",
  "title": "Design Review",
  "description": "Finalizing the UI/UX for the mobile app.",
  "participants": "Alice, Bob, Charlie",
  "time_minutes": 1440,
  "duration_mins": 45,
  "priority": "medium",
  "location": "Virtual Hub"
}}

3. CHAT/PLAN (For general intelligence, planning, or complex analysis):
{{
  "type": "chat",
  "response": "Your sophisticated agentic response here. Use markdown for lists and bolding."
}}

[TIME REFERENCE]
Current System Time: {current_time}
User's Timezone: UTC

[INSTRUCTIONS]
- If the user says 'remind me in 5 minutes', set 'time_minutes' to 5.
- If the user says 'remind me tomorrow', calculate the minutes from NOW and set 'time_minutes'.
- If the user says 'remind me at 3 PM' and it's 2 PM, set 'time_minutes' to 60.
- BE PRECISE.
"""

# ──────────────────────────────────────────────────────────────────────────────
# CORE AI FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def clean_json_string(raw_text):
    """
    Cleans markdown code blocks and whitespace from Ollama responses to ensure valid JSON.
    """
    if not raw_text:
        return "{}"
    
    # Remove markdown code blocks (```json ... ```)
    clean_text = re.sub(r'```json\s*|\s*```', '', raw_text)
    clean_text = re.sub(r'```\s*|\s*```', '', clean_text)
    
    # Extract only the content between the first { and the last }
    start = clean_text.find("{")
    end = clean_text.rfind("}") + 1
    if start != -1 and end > start:
        return clean_text[start:end]
    
    return clean_text.strip()

def ask_ai(prompt, system_context="", memory_context=""):
    """
    Robust AI execution engine with full error handling and JSON enforcement.
    """
    now = timezone.now()
    formatted_time = now.strftime("%A, %d %B %Y, %I:%M %p")
    
    full_prompt = f"{ZEUS_SYSTEM_PROMPT.format(current_time=formatted_time)}\n\n"
    
    if memory_context:
        full_prompt += f"[MEMORIES]\n{memory_context}\n\n"
    
    if system_context:
        full_prompt += f"[CURRENT CONTEXT]\n{system_context}\n\n"
        
    full_prompt += f"USER MESSAGE: {prompt}\n"
    full_prompt += "ZEUS RESPONSE (JSON):"

    try:
        logger.info(f"Calling Ollama with prompt: {prompt[:50]}...")
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": full_prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.4, # Lower temperature for stable JSON
                    "num_predict": 1024
                }
            },
            timeout=45 # Increased timeout for Llama 3
        )
        
        response.raise_for_status()
        raw_data = response.json()
        
        # Prevent KeyError: 'response'
        if 'response' not in raw_data:
            logger.error(f"Unexpected Ollama Response Structure: {raw_data}")
            return {"type": "chat", "response": "SYSTEM ERROR: Invalid response structure from AI engine."}
            
        result_text = raw_data.get("response", "")
        logger.info(f"Raw AI Response: {result_text[:100]}...")
        
        cleaned_json = clean_json_string(result_text)
        parsed_data = json.loads(cleaned_json)
        
        logger.info(f"Parsed AI JSON: {parsed_data.get('type')}")
        return parsed_data

    except requests.exceptions.ConnectionError:
        logger.error("Ollama connection failed. Is the server running?")
        return {
            "type": "chat",
            "response": "⚠️ **SYSTEM OFFLINE**: ZEUS Neural Core (Ollama) is not detected. Ensure `ollama serve` is active."
        }
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out.")
        return {
            "type": "chat",
            "response": "⏳ **CORE TIMEOUT**: The AI processing took too long. I am recalibrating. Please try again."
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {e} | Raw: {result_text}")
        return {
            "type": "chat",
            "response": "🧩 **CORE FRAGMENTATION**: I generated an invalid data structure. Let's try again in plain language."
        }
    except Exception as e:
        logger.error(f"Unexpected ZEUS Error: {str(e)}")
        return {
            "type": "chat",
            "response": "⚡ **UNEXPECTED ANOMALY**: An internal error occurred in the neural pathways. Manual override required."
        }

def chatbot_response(message, user=None):
    """
    Agentic workflow controller. Manages memory, context, and execution.
    """
    system_ctx = ""
    memory_ctx = ""

    if user:
        # 1. Retrieve relevant memories for context
        memory_ctx = get_memory_context(user, message)

        # 2. Build current schedule context (Next 3 upcoming meetings)
        from .models import Meeting
        upcoming = Meeting.objects.filter(
            user=user,
            status='upcoming',
            meeting_at__gte=timezone.now()
        ).order_by('meeting_at')[:3]

        if upcoming.exists():
            system_ctx = "Upcoming User Schedule:\n"
            for m in upcoming:
                system_ctx += f"- {m.title} at {m.meeting_at.strftime('%H:%M')} (Priority: {m.priority})\n"

    # 3. Process with AI Brain
    ai = ask_ai(message, system_context=system_ctx, memory_context=memory_ctx)

    # 4. Background Memory Extraction
    if user:
        try:
            extract_memories_from_text(user, message)
        except Exception as e:
            logger.warning(f"Memory extraction failed: {e}")

    # 5. EXECUTION & ROUTING
    resp_type = ai.get("type", "chat")

    # [R] REMINDER EXECUTION
    if resp_type == "reminder":
        minutes = ai.get("time_minutes", 10)
        try:
            # Ensure minutes is an integer
            minutes = int(minutes)
        except:
            minutes = 10
            
        remind_time = timezone.now() + timedelta(minutes=minutes)
        
        return {
            "type": "reminder",
            "task": ai.get("task", "Notification"),
            "remind_at": remind_time,
            "priority": ai.get("priority", "medium"),
            "ai_note": ai.get("ai_note", "Synchronizing reminder with neural core.")
        }

    # [M] MEETING EXECUTION
    elif resp_type == "meeting":
        try:
            minutes = int(ai.get("time_minutes", 60))
        except:
            minutes = 60
            
        meeting_time = timezone.now() + timedelta(minutes=minutes)
        
        return {
            "type": "meeting",
            "title": ai.get("title", "Strategic Meeting"),
            "description": ai.get("description", ""),
            "participants": ai.get("participants", ""),
            "meeting_at": meeting_time,
            "duration_mins": ai.get("duration_mins", 30),
            "priority": ai.get("priority", "medium"),
            "location": ai.get("location", "Virtual Sync")
        }

    # [C] CHAT/PLAN EXECUTION
    else:
        return {
            "type": "chat",
            "response": ai.get("response", "I am standing by for your next directive.")
        }

# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS ENGINE
# ──────────────────────────────────────────────────────────────────────────────

def analyze_user_behavior(user):
    """
    Deeper behavioral analytics for the AI Analysis dashboard.
    """
    from .models import Meeting, Reminder, UserBehavior
    
    logger.info(f"Starting behavioral analysis for user: {user.username}")

    meetings = Meeting.objects.filter(user=user)
    reminders = Reminder.objects.filter(user=user)

    total = meetings.count()
    completed = meetings.filter(status='completed').count()
    cancelled = meetings.filter(status='cancelled').count()

    # Peak hour analysis
    hours = [m.meeting_at.hour for m in meetings if m.meeting_at]
    most_common_hour = max(set(hours), key=hours.count) if hours else 10

    # Reminder lead analysis
    lead_times = []
    for r in reminders.filter(meeting__isnull=False):
        if r.meeting:
            delta = (r.meeting.meeting_at - r.created_at).total_seconds() / 60
            if delta > 0:
                lead_times.append(delta)
    avg_lead = int(sum(lead_times) / len(lead_times)) if lead_times else 15

    # Memory injection
    memory_ctx = get_memory_context(user, "productivity behavior habits")

    analysis_prompt = f"""
Analyze this productivity data and provide a strategic summary:
- Total Engagements: {total}
- Success Rate: {int((completed/total)*100) if total > 0 else 0}%
- Failure/Cancellation Rate: {int((cancelled/total)*100) if total > 0 else 0}%
- Peak Cognitive Hours: {most_common_hour}:00
- Strategic Prep Time (Reminder Lead): {avg_lead} minutes

Respond with type "chat" providing a sophisticated analysis and actionable improvement steps.
"""

    result = ask_ai(analysis_prompt, memory_context=memory_ctx)

    # Persistence
    behavior, _ = UserBehavior.objects.get_or_create(user=user)
    behavior.most_productive_hour = most_common_hour
    behavior.preferred_reminder_lead_mins = avg_lead
    behavior.total_meetings = total
    behavior.completed_meetings = completed
    behavior.cancelled_meetings = cancelled
    
    response_text = result.get("response", result.get("summary", "Analysis complete."))
    behavior.ai_summary = response_text
    behavior.last_analyzed = timezone.now()
    behavior.save()

    return {
        "type": "analysis",
        "summary": response_text,
        "suggestions": result.get("suggestions", [])
    }