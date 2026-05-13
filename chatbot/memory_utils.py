from .models import Memory
from django.db.models import Q
import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

def save_memory(user, category, key, value):
    """
    Saves or updates a memory for a user.
    """
    memory, created = Memory.objects.update_or_create(
        user=user,
        category=category,
        key=key.lower().strip(),
        defaults={'value': value.strip()}
    )
    return memory, created

def get_user_memories(user, category=None):
    """
    Retrieves all memories for a user, optionally filtered by category.
    """
    memories = Memory.objects.filter(user=user)
    if category:
        memories = memories.filter(category=category)
    return memories

def search_relevant_memories(user, query, limit=5):
    """
    Simple keyword-based search for relevant memories.
    In a real-world scenario, this could use embeddings/vector search.
    """
    # For now, we use a simple keyword search across key and value
    words = query.lower().split()
    q_objects = Q()
    for word in words:
        if len(word) > 3:  # Only search for meaningful words
            q_objects |= Q(key__icontains=word) | Q(value__icontains=word)
    
    if not q_objects:
        return Memory.objects.filter(user=user).order_by('-updated_at')[:limit]
        
    return Memory.objects.filter(Q(user=user) & q_objects).order_by('-updated_at')[:limit]

def clean_json_list(raw_text):
    """
    Cleans markdown code blocks and ensures we get a valid JSON list.
    """
    if not raw_text:
        return "[]"
    clean_text = re.sub(r'```json\s*|\s*```', '', raw_text)
    clean_text = re.sub(r'```\s*|\s*```', '', clean_text)
    start = clean_text.find("[")
    end = clean_text.rfind("]") + 1
    if start != -1 and end > start:
        return clean_text[start:end]
    return clean_text.strip()

def extract_memories_from_text(user, text):
    """
    Uses Ollama to extract potential memories from user text.
    """
    import re # Ensure re is available
    extract_prompt = f"""
    Analyze the following user message and extract any important facts, preferences, habits, or schedule details.
    
    User Message: "{text}"
    
    Return ONLY a valid JSON list of objects with "category", "key", and "value".
    Categories: "preference", "schedule", "personal", "work", "study".
    
    Example:
    [
      {{"category": "preference", "key": "coffee", "value": "likes it black"}},
      {{"category": "schedule", "key": "workout", "value": "gym at 7am"}}
    ]
    
    If nothing is worth remembering, return exactly [].
    """
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": extract_prompt,
                "stream": False,
                "format": "json"
            },
            timeout=25
        )
        response.raise_for_status()
        raw_response = response.json().get("response", "[]")
        
        cleaned_json = clean_json_list(raw_response)
        memories_data = json.loads(cleaned_json)
        
        if not isinstance(memories_data, list):
            return []
            
        saved_memories = []
        for item in memories_data:
            cat = item.get("category", "personal")
            key = item.get("key")
            val = item.get("value")
            if key and val:
                mem, created = save_memory(user, cat, key, val)
                saved_memories.append(mem)
        return saved_memories
    except Exception as e:
        print(f"ZEUS Memory Extraction Anomaly: {e}")
        return []

def get_memory_context(user, query):
    """
    Constructs a context string from relevant memories to inject into the prompt.
    """
    relevant = search_relevant_memories(user, query)
    if not relevant.exists():
        return ""
    
    context = "\n--- RELEVANT MEMORIES ---\n"
    for m in relevant:
        context += f"- {m.category.capitalize()}: {m.key} -> {m.value}\n"
    return context
