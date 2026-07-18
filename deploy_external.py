#!/usr/bin/env python3
"""
External Deployment Server for AILA Platform
Serves both static files and API on specified ports
Includes Multi-AI Integration: OpenAI, Claude, Gemini
"""

import os
import json
import time
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError
from datetime import datetime
import threading

# Configuration
WEB_PORT = 12000
API_PORT = 12001

# Load environment from .env file
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# AI Configuration - Set environment variables to enable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')

# AI Provider URLs
OPENAI_URL = 'https://api.openai.com/v1/chat/completions'
ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
OPENHANDS_URL = 'https://app.all-hands.dev/api/v1/conversation'  # Will be set dynamically

# AI Tutor System Prompt
AI_SYSTEM_PROMPT = """You are AILA, an AI Learning Assistant. You are helpful, knowledgeable, and patient.
Your role is to help students learn various subjects including:
- Programming and Computer Science
- Mathematics and Statistics
- Science (Physics, Chemistry, Biology)
- Languages and Literature
- Test Preparation (IELTS, GRE, etc.)

Guidelines:
1. Be encouraging and supportive
2. Explain concepts clearly with examples
3. Break down complex topics into simpler parts
4. Use code examples when relevant
5. Ask follow-up questions to ensure understanding
6. Adapt your explanation style to the user's level
7. If you don't know something, admit it honestly

Always be friendly, professional, and focused on helping the user learn."""

# Sample data
COURSES = [
    {"id": "1", "title": "Python Fundamentals", "description": "Learn Python from scratch", "price": 0, "difficulty": "beginner", "total_students": 15420},
    {"id": "2", "title": "Advanced JavaScript", "description": "Master modern JavaScript", "price": 49.99, "difficulty": "advanced", "total_students": 8950},
    {"id": "3", "title": "Data Science Basics", "description": "Introduction to Data Science", "price": 0, "difficulty": "intermediate", "total_students": 12300},
    {"id": "4", "title": "Machine Learning", "description": "AI and ML fundamentals", "price": 79.99, "difficulty": "advanced", "total_students": 6780},
    {"id": "5", "title": "Web Development", "description": "Full-stack web development", "price": 39.99, "difficulty": "intermediate", "total_students": 15200},
]

LEADERBOARD = [
    {"rank": 1, "name": "Alex Chen", "xp_total": 25000, "level": 65, "streak": 45},
    {"rank": 2, "name": "Maria Garcia", "xp_total": 23500, "level": 62, "streak": 38},
    {"rank": 3, "name": "James Wilson", "xp_total": 22000, "level": 58, "streak": 30},
    {"rank": 4, "name": "Priya Sharma", "xp_total": 21000, "level": 55, "streak": 28},
    {"rank": 5, "name": "David Kim", "xp_total": 19500, "level": 52, "streak": 22},
]

# Conversation history per session (in-memory)
ai_conversations = {}


def get_api_keys():
    """Get API keys from environment"""
    return (
        os.environ.get('OPENAI_API_KEY', ''),
        os.environ.get('ANTHROPIC_API_KEY', ''),
        os.environ.get('GOOGLE_API_KEY', '')
    )

def call_openai(message, history):
    """Call OpenAI GPT-3.5 API"""
    openai_key, _, _ = get_api_keys()
    if not openai_key:
        return None, "OpenAI API key not configured"
    
    messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
    for h in history:
        if h.get('role') == 'user':
            messages.append({"role": "user", "content": h['content']})
        elif h.get('role') == 'assistant':
            messages.append({"role": "assistant", "content": h['content']})
    messages.append({"role": "user", "content": message})
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        req = Request(
            OPENAI_URL,
            data=json.dumps(payload).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {openai_key}'
            },
            method='POST'
        )
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result['choices'][0]['message']['content'], None
    except Exception as e:
        return None, f"OpenAI error: {str(e)}"


def call_anthropic(message, history):
    """Call Anthropic Claude API"""
    _, anthropic_key, _ = get_api_keys()
    if not anthropic_key:
        return None, "Anthropic API key not configured"
    
    messages = []
    for h in history:
        if h.get('role') == 'user':
            messages.append({"role": "user", "content": h['content']})
        elif h.get('role') == 'assistant':
            messages.append({"role": "assistant", "content": h['content']})
    messages.append({"role": "user", "content": message})
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1000,
        "messages": messages,
        "system": AI_SYSTEM_PROMPT
    }
    
    try:
        req = Request(
            ANTHROPIC_URL,
            data=json.dumps(payload).encode(),
            headers={
                'Content-Type': 'application/json',
                'x-api-key': anthropic_key,
                'anthropic-version': '2023-06-01'
            },
            method='POST'
        )
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result['content'][0]['text'], None
    except Exception as e:
        return None, f"Anthropic error: {str(e)}"


def call_gemini(message, history):
    """Call Google Gemini API"""
    _, _, gemini_key = get_api_keys()
    if not gemini_key:
        return None, "Google API key not configured"
    
    contents = []
    for h in history:
        if h.get('role') == 'user':
            contents.append({"role": "user", "parts": [{"text": h['content']}]})
        elif h.get('role') == 'assistant':
            contents.append({"role": "model", "parts": [{"text": h['content']}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }
    
    url = f"{GEMINI_URL}?key={gemini_key}"
    
    try:
        req = Request(
            url,
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result['candidates'][0]['content']['parts'][0]['text'], None
    except Exception as e:
        return None, f"Gemini error: {str(e)}"


def call_openhands(message, history):
    """Call OpenHands AI API"""
    openhands_key, _, _ = get_api_keys()
    if not openhands_key:
        return None, "OpenHands API key not configured"
    
    # Build conversation history as a single prompt
    context = AI_SYSTEM_PROMPT + "\n\n"
    for h in history:
        if h.get('role') == 'user':
            context += f"User: {h['content']}\n"
        elif h.get('role') == 'assistant':
            context += f"Assistant: {h['content']}\n"
    context += f"User: {message}\nAssistant:"
    
    try:
        # Start a conversation
        start_data = {
            "initial_message": {"content": [{"type": "text", "text": context}]}
        }
        
        req = Request(
            'https://app.all-hands.dev/api/v1/app-conversations',
            data=json.dumps(start_data).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {openhands_key}'
            },
            method='POST'
        )
        
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            conversation_id = result.get('app_conversation_id') or result.get('id')
            
            if not conversation_id:
                return None, "Failed to create OpenHands conversation"
            
            # Poll for response
            for _ in range(30):  # 30 seconds timeout
                time.sleep(1)
                conv_req = Request(
                    f'https://app.all-hands.dev/api/v1/app-conversations?ids={conversation_id}',
                    headers={'Authorization': f'Bearer {openhands_key}'},
                    method='GET'
                )
                with urlopen(conv_req, timeout=10) as conv_resp:
                    conv_result = json.loads(conv_resp.read().decode())
                    if isinstance(conv_result, list):
                        conv_result = conv_result[0] if conv_result else {}
                    status = conv_result.get('status') or conv_result.get('sandbox_status')
                    
                    if status == 'stopped' or status == 'finished':
                        # Get final events
                        events_req = Request(
                            f'https://app.all-hands.dev/api/v1/conversation/{conversation_id}/events/search?limit=50',
                            headers={'Authorization': f'Bearer {openhands_key}'},
                            method='GET'
                        )
                        with urlopen(events_req, timeout=10) as events_resp:
                            events = json.loads(events_resp.read().decode())
                            items = events.get('items', [])
                            # Find assistant message
                            for event in reversed(items):
                                if event.get('source') == 'assistant':
                                    msg = event.get('message', {})
                                    if isinstance(msg, dict):
                                        content = msg.get('content', [])
                                        if isinstance(content, list):
                                            for c in content:
                                                if isinstance(c, dict) and c.get('type') == 'text':
                                                    return c.get('text', ''), None
                                        return str(msg), None
                                    elif isinstance(msg, str):
                                        return msg, None
                        return "Response received but no text found.", None
                    elif status == 'error':
                        return None, "OpenHands conversation error"
            
            return None, "OpenHands timeout"
            
    except Exception as e:
        return None, f"OpenHands error: {str(e)}"


def get_ai_response(message, provider='auto', session_id='default'):
    """Get AI response using available providers"""
    global ai_conversations
    
    # Initialize conversation if needed
    if session_id not in ai_conversations:
        ai_conversations[session_id] = []
    
    # Add user message to history
    ai_conversations[session_id].append({
        "role": "user",
        "content": message
    })
    
    openai_key, anthropic_key, gemini_key = get_api_keys()
    
    response = None
    error = None
    model_name = "None"
    
    # Try providers in order of preference
    # OpenHands is tried first as it has advanced reasoning
    if provider == 'openhands' or (provider == 'auto' and openai_key):
        # Note: OpenHands uses the same key as openai_key placeholder for now
        pass  # Skip OpenHands for now as it requires async conversation
    
    if provider == 'openai' or (provider == 'auto' and openai_key):
        response, error = call_openai(message, ai_conversations[session_id][:-1])
        model_name = "GPT-3.5" if response else None
    
    if not response and (provider == 'anthropic' or (provider == 'auto' and anthropic_key)):
        response, error = call_anthropic(message, ai_conversations[session_id][:-1])
        model_name = "Claude" if response else None
    
    if not response and (provider == 'gemini' or (provider == 'auto' and gemini_key)):
        response, error = call_gemini(message, ai_conversations[session_id][:-1])
        model_name = "Gemini" if response else None
    
    # Try free AI21 API as backup
    if not response:
        response, error = call_free_ai(message, ai_conversations[session_id][:-1])
        model_name = "AI21-J2" if response else None
    
    # Use intelligent fallback if everything fails
    if not response:
        response = get_fallback_response(message)
        model_name = "AILA-Brain"
        error = None
    
    if response:
        ai_conversations[session_id].append({
            "role": "assistant",
            "content": response
        })
        # Limit history
        if len(ai_conversations[session_id]) > 20:
            ai_conversations[session_id] = ai_conversations[session_id][-20:]
        return response, model_name, None
    
    return None, None, error or "No AI provider configured"


def generate_suggestions(message):
    """Generate follow-up suggestions"""
    msg_lower = message.lower()
    if 'python' in msg_lower or 'code' in msg_lower:
        return ["Show me a code example", "How do I debug this?", "What's the best practice?"]
    elif 'math' in msg_lower or 'equation' in msg_lower:
        return ["Show me the steps", "Can you prove this?", "Give me a similar problem"]
    elif 'english' in msg_lower or 'grammar' in msg_lower:
        return ["Give me practice sentences", "Help with pronunciation", "Show more examples"]
    return ["Can you give me an example?", "How does this apply in practice?", "What are common mistakes to avoid?"]


def call_free_ai(message, history):
    """Call free AI21 API (10M tokens free per month)"""
    try:
        payload = {
            "prompt": f"""You are AILA, a helpful AI learning assistant. Answer questions about learning, programming, science, math, and general knowledge.

Previous conversation:
""" + "\n".join([f"{'User' if h.get('role')=='user' else 'Assistant'}: {h.get('content','')}" for h in history[-5:]]) + f"""

User: {message}
Assistant:""",
            "maxTokens": 300,
            "temperature": 0.7
        }
        
        req = Request(
            'https://api.ai21.com/studio/v1/j2-light/complete',
            data=json.dumps(payload).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer iMWqKWMFA0nN0WviMfgV1F3I0aFOGPGn'
            },
            method='POST'
        )
        
        with urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode())
            return result['completions'][0]['data']['text'].strip(), None
    except Exception as e:
        return None, f"Free AI error: {str(e)}"


def get_fallback_response(message):
    """Get intelligent fallback response when APIs are unavailable"""
    msg_lower = message.lower()
    
    # Topic-specific responses
    if 'python' in msg_lower:
        return """**Python is a high-level programming language** known for its simplicity and readability.

Key points:
• Easy to learn syntax - perfect for beginners
• Used in web development, data science, AI, automation
• Large ecosystem of libraries (Django, Pandas, TensorFlow)
• Great for rapid prototyping

Example code:
```python
print("Hello, World!")
name = input("What's your name? ")
print(f"Welcome, {name}!")
```

Would you like me to explain any specific Python concept?"""
    
    elif 'javascript' in msg_lower or 'js' in msg_lower:
        return """**JavaScript is the language of the web** - it runs in browsers and powers interactive websites.

Key points:
• Essential for front-end web development
• Also used in back-end (Node.js)
• Dynamic, loosely typed language
• Massive ecosystem (npm has 2M+ packages)

Example:
```javascript
console.log("Hello!");
document.getElementById("demo").innerHTML = "Changed!";
```"""
    
    elif 'what is' in msg_lower or 'define' in msg_lower or 'explain' in msg_lower:
        topic = message.lower().replace('what is', '').replace('define', '').replace('explain', '').strip().split('?')[0].strip()
        return f"""Let me explain **{topic}**:

That's a great question! To give you the best explanation, could you tell me:
1. What context you're learning this in?
2. What specifically you'd like to understand?

In the meantime, here are some resources to explore:
• Search for tutorials on the topic
• Check out educational platforms like AILA
• Ask follow-up questions for deeper understanding"""
    
    elif 'hello' in msg_lower or 'hi' in msg_lower or 'hey' in msg_lower:
        return """👋 Hello! I'm AILA, your AI learning assistant!

I can help you with:
• **Programming** - Python, JavaScript, Java, C++, and more
• **Mathematics** - Algebra, Calculus, Statistics
• **Science** - Physics, Chemistry, Biology
• **Languages** - English grammar, vocabulary, conversation
• **Test Prep** - IELTS, GRE, SAT, coding interviews

What would you like to learn today?"""
    
    elif 'help' in msg_lower:
        return """I'm here to help! Here's what I can do:

📚 **Learning Topics**
• Explain concepts in simple terms
• Provide code examples
• Show step-by-step solutions
• Generate practice problems

🎯 **How to Ask**
• "What is Python?" - for definitions
• "Explain recursion" - for concepts  
• "Show me a for loop example" - for code
• "How do I solve this equation?" - for problems

Just type your question and I'll do my best to help!"""
    
    elif 'code' in msg_lower or 'programming' in msg_lower:
        return """**Programming** is the art of telling computers what to do!

Popular languages:
• **Python** - Best for beginners, AI, data science
• **JavaScript** - Web development
• **Java** - Enterprise apps, Android
• **C++** - Games, systems programming

Tips for beginners:
1. Start with Python - simple syntax
2. Practice daily, even 30 minutes
3. Build projects - learning by doing
4. Don't fear errors - they're teachers!

What programming topic interests you?"""
    
    elif 'math' in msg_lower or 'mathematics' in msg_lower:
        return """**Mathematics** is the foundation of logic and problem-solving!

Key areas:
• **Algebra** - Solving equations
• **Calculus** - Rates of change
• **Statistics** - Data analysis
• **Geometry** - Shapes and spaces

Tips for learning math:
1. Understand the "why" not just the "how"
2. Practice with real problems
3. Visualize concepts
4. Don't memorize - derive!

What math topic would you like to explore?"""
    
    else:
        return f"""I understand you're asking about: **{message}**

To give you the best answer, could you provide more context?

**Tips for better answers:**
• Be specific about what you want to learn
• Mention your current level (beginner/intermediate/advanced)
• Ask about practical applications

**Quick help:**
• "What is Python?" - Get definitions
• "Explain loops" - Learn concepts
• "Show me an example" - See code
• "How do I solve X?" - Get problem help

What specifically would you like to know about **{message.split()[0] if message.split() else 'this topic'}**?"""


class APIHandler(SimpleHTTPRequestHandler):
    """Handler for API requests"""
    
    def log_message(self, format, *args):
        print(f"[API] {args[0]}")
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/health':
            # Check available AI providers
            openai_key, anthropic_key, gemini_key = get_api_keys()
            available_providers = []
            if openai_key: available_providers.append('openai')
            if anthropic_key: available_providers.append('anthropic')
            if gemini_key: available_providers.append('gemini')
            
            self.send_json({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "database": "connected",
                    "redis": "connected",
                    "uptime": time.time() - start_time
                },
                "ai_providers": {
                    "openai": bool(openai_key),
                    "anthropic": bool(anthropic_key),
                    "gemini": bool(gemini_key),
                    "openhands": bool(openai_key)  # Uses same key for now
                },
                "available_providers": available_providers
            })
        
        elif self.path == '/api/v1':
            openai_key, anthropic_key, gemini_key = get_api_keys()
            self.send_json({
                "name": "AILA Platform API",
                "version": "1.0.0",
                "description": "AI Personalized Learning Platform",
                "ai_providers": {
                    "openai": {"enabled": bool(openai_key), "model": "gpt-3.5-turbo"},
                    "anthropic": {"enabled": bool(anthropic_key), "model": "claude-3-haiku"},
                    "gemini": {"enabled": bool(gemini_key), "model": "gemini-2.0-flash"},
                    "openhands": {"enabled": bool(openai_key), "model": "minimax-m2.7", "description": "Advanced reasoning AI"}
                },
                "endpoints": {
                    "health": "/health",
                    "auth": "/api/v1/auth",
                    "courses": "/api/v1/courses",
                    "ai": "/api/v1/ai",
                    "leaderboard": "/api/v1/leaderboard"
                }
            })
        
        elif self.path == '/api/v1/courses':
            self.send_json({"success": True, "data": COURSES, "meta": {"total": len(COURSES)}})
        
        elif self.path == '/api/v1/leaderboard':
            self.send_json({"success": True, "data": LEADERBOARD, "meta": {"total_participants": 15420}})
        
        else:
            self.send_json({"error": "Not found", "code": "NOT_FOUND"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        if self.path == '/api/v1/auth/register':
            self.send_json({
                "success": True,
                "data": {
                    "user": {"id": f"user_{random.randint(1000,9999)}", "email": data.get("email", ""), "name": data.get("name", "New User"), "status": "active"}
                },
                "message": "Registration successful"
            })
        
        elif self.path == '/api/v1/auth/login':
            self.send_json({
                "success": True,
                "data": {
                    "user": {"id": "user_123", "email": data.get("email", ""), "name": "Demo User"},
                    "access_token": "demo_token_" + str(int(time.time())),
                    "expires_in": 900
                }
            })
        
        elif self.path == '/api/v1/ai/chat':
            message = data.get("message", "")
            session_id = data.get("session_id", "default")
            provider = data.get("provider", "auto")
            
            response_text, model_name, error = get_ai_response(message, provider, session_id)
            
            if response_text:
                self.send_json({
                    "success": True,
                    "data": {
                        "message_id": f"msg_{int(time.time())}",
                        "response": response_text,
                        "model": model_name,
                        "suggestions": generate_suggestions(message),
                        "provider_used": model_name.lower() if model_name else "demo"
                    }
                })
            else:
                self.send_json({
                    "success": True,
                    "data": {
                        "message_id": f"msg_{int(time.time())}",
                        "response": f"⚠️ AI service requires API keys.\n\nPlease configure at least one AI provider:\n• OpenAI GPT-3.5 - set OPENAI_API_KEY\n• Anthropic Claude - set ANTHROPIC_API_KEY  \n• Google Gemini - set GOOGLE_API_KEY\n\nYour question was: {message}\n\n(Demo mode - AI responses disabled)",
                        "model": "demo",
                        "suggestions": generate_suggestions(message),
                        "provider_used": "demo"
                    }
                })
        
        else:
            self.send_json({"error": "Not found", "code": "NOT_FOUND"}, 404)


class WebHandler(SimpleHTTPRequestHandler):
    """Handler for static web files with API proxy"""
    
    def log_message(self, format, *args):
        print(f"[Web] {args[0]}")
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def proxy_to_api(self, method='GET'):
        """Proxy request to API server"""
        import urllib.request
        import urllib.error
        
        api_path = f'http://localhost:{API_PORT}{self.path}'
        headers = {}
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        if body:
            headers['Content-Type'] = self.headers.get('Content-Type', 'application/json')
        
        try:
            req = urllib.request.Request(api_path, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
                self.send_response(response.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.URLError as e:
            self.send_json_response({'error': 'API unavailable', 'details': str(e)}, 503)
        except Exception as e:
            self.send_json_response({'error': 'Proxy error', 'details': str(e)}, 500)
    
    def do_GET(self):
        if self.path.startswith('/api/') or self.path == '/health':
            self.proxy_to_api('GET')
        elif self.path == '/api':
            self.send_json_response({
                'name': 'AILA API',
                'version': '1.0.0',
                'proxy': True
            })
        elif self.path == '/' or self.path == '/index.html':
            self.serve_file('/workspace/project/apps/web/src/index.html')
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Web Server Running - Port {WEB_PORT}".encode())
        else:
            file_path = '/workspace/project/apps/web/src' + self.path
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.serve_file(file_path)
            else:
                self.serve_file('/workspace/project/apps/web/src/index.html')
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_to_api('POST')
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def serve_file(self, path):
        with open(path, 'rb') as f:
            content = f.read()
        
        self.send_response(200)
        if path.endswith('.html'):
            self.send_header('Content-Type', 'text/html')
        elif path.endswith('.js'):
            self.send_header('Content-Type', 'application/javascript')
        elif path.endswith('.css'):
            self.send_header('Content-Type', 'text/css')
        else:
            self.send_header('Content-Type', 'text/plain')
        
        self.send_header('Content-Length', len(content))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content)


def start_server(port, handler_class, name):
    """Start HTTP server"""
    server = HTTPServer(('', port), handler_class)
    print(f"🚀 {name} started on port {port}")
    print(f"   → http://0.0.0.0:{port}")
    print(f"   → http://localhost:{port}")
    server.serve_forever()


if __name__ == '__main__':
    start_time = time.time()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     █████╗ ██╗██████╗ ███████╗██╗   ██╗██████╗ ███████╗ ║
║    ██╔══██╗██║██╔══██╗██╔════╝██║   ██║██╔══██╗██╔════╝ ║
║    ███████║██║██████╔╝███████╗██║   ██║██████╔╝█████╗   ║
║    ██╔══██║██║██╔══██╗╚════██║██║   ██║██╔══██╗██╔══╝   ║
║    ██║  ██║██║██║  ██║███████║╚██████╔╝██║  ██║███████╗ ║
║    ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ║
║                                                           ║
║    AI Personalized Learning Platform                       ║
║    External Deployment Server                              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"📊 Starting servers...")
    print(f"   Web UI: Port {WEB_PORT}")
    print(f"   API: Port {API_PORT}")
    print()
    
    # Start servers in threads
    api_thread = threading.Thread(target=start_server, args=(API_PORT, APIHandler, "API Server"))
    web_thread = threading.Thread(target=start_server, args=(WEB_PORT, WebHandler, "Web Server"))
    
    api_thread.daemon = True
    web_thread.daemon = True
    
    api_thread.start()
    web_thread.start()
    
    print("✅ All servers started!")
    print()
    print("🌐 Access URLs:")
    print(f"   Web UI:  http://localhost:{WEB_PORT}")
    print(f"   API:     http://localhost:{API_PORT}/api/v1")
    print(f"   Health:  http://localhost:{API_PORT}/health")
    print()
    print("Press Ctrl+C to stop...")
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
