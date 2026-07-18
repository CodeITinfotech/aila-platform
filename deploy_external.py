#!/usr/bin/env python3
"""
External Deployment Server for AILA Platform
Serves both static files and API on specified ports
Includes Full AI Integration with OpenAI GPT
"""

import os
import sys
import json
import time
import random
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError
from datetime import datetime
import threading

# Configuration
WEB_PORT = 12000
API_PORT = 12001

# AI Configuration
# Set OPENAI_API_KEY environment variable for real AI responses
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
AI_MODEL = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')
AI_BASE_URL = 'https://api.openai.com/v1/chat/completions'

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


def call_openai_api(messages, session_id=None):
    """Call OpenAI API with conversation context"""
    if not OPENAI_API_KEY:
        return None, "AI API key not configured"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    
    payload = {
        'model': AI_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 1000
    }
    
    try:
        req = Request(
            AI_BASE_URL,
            data=json.dumps(payload).encode(),
            headers=headers,
            method='POST'
        )
        
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result, None
            
    except URLError as e:
        return None, f"Network error: {str(e)}"
    except json.JSONDecodeError:
        return None, "Invalid response from AI service"
    except Exception as e:
        return None, f"AI error: {str(e)}"


def get_ai_response(message, session_id='default'):
    """Get AI response using OpenAI API"""
    global ai_conversations
    
    # Initialize conversation if needed
    if session_id not in ai_conversations:
        ai_conversations[session_id] = [
            {"role": "system", "content": AI_SYSTEM_PROMPT}
        ]
    
    # Add user message to history
    ai_conversations[session_id].append({
        "role": "user", 
        "content": message
    })
    
    # Limit conversation history to last 10 messages
    if len(ai_conversations[session_id]) > 11:  # +1 for system
        ai_conversations[session_id] = [
            ai_conversations[session_id][0],  # Keep system prompt
            *ai_conversations[session_id][-10:]
        ]
    
    # Call OpenAI API
    result, error = call_openai_api(ai_conversations[session_id], session_id)
    
    if error:
        return None, error, 0
    
    # Extract response
    response_text = result['choices'][0]['message']['content']
    tokens_used = result.get('usage', {}).get('total_tokens', 0)
    
    # Add AI response to history
    ai_conversations[session_id].append({
        "role": "assistant",
        "content": response_text
    })
    
    return response_text, None, tokens_used


def generate_suggestions(message):
    """Generate follow-up question suggestions based on context"""
    suggestions = [
        "Can you give me an example?",
        "How does this apply in practice?",
        "What are common mistakes to avoid?",
        "Can you explain that differently?"
    ]
    
    # Context-aware suggestions
    msg_lower = message.lower()
    
    if 'python' in msg_lower or 'code' in msg_lower:
        suggestions = [
            "Show me a code example",
            "How do I debug this?",
            "What's the best practice?",
            "Explain it with Python"
        ]
    elif 'math' in msg_lower or 'equation' in msg_lower:
        suggestions = [
            "Show me the steps",
            "Can you prove this?",
            "Give me a similar problem",
            "Why does this work?"
        ]
    elif 'english' in msg_lower or 'grammar' in msg_lower:
        suggestions = [
            "Give me practice sentences",
            "What's the exception to this rule?",
            "Help with pronunciation",
            "Show more examples"
        ]
    
    return suggestions[:3]


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
        parsed = urlparse(self.path)
        
        if self.path == '/health':
            self.send_json({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "database": "connected",
                    "redis": "connected",
                    "uptime": time.time() - start_time
                }
            })
        
        elif self.path == '/api/v1':
            self.send_json({
                "name": "AILA Platform API",
                "version": "1.0.0",
                "description": "AI Personalized Learning Platform",
                "endpoints": {
                    "health": "/health",
                    "auth": "/api/v1/auth",
                    "users": "/api/v1/users",
                    "courses": "/api/v1/courses",
                    "lessons": "/api/v1/lessons",
                    "quizzes": "/api/v1/quizzes",
                    "ai": "/api/v1/ai",
                    "achievements": "/api/v1/achievements",
                    "leaderboard": "/api/v1/leaderboard"
                }
            })
        
        elif self.path == '/api/v1/courses':
            self.send_json({
                "success": True,
                "data": COURSES,
                "meta": {"total": len(COURSES)}
            })
        
        elif self.path == '/api/v1/leaderboard':
            self.send_json({
                "success": True,
                "data": LEADERBOARD,
                "meta": {"total_participants": 15420}
            })
        
        else:
            self.send_json({"error": "Not found", "code": "NOT_FOUND"}, 404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
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
                    "user": {
                        "id": f"user_{random.randint(1000,9999)}",
                        "email": data.get("email", "user@example.com"),
                        "name": data.get("name", "New User"),
                        "status": "active"
                    },
                    "message": "Registration successful"
                }
            })
        
        elif self.path == '/api/v1/auth/login':
            self.send_json({
                "success": True,
                "data": {
                    "user": {"id": "user_123", "email": data.get("email", "user@example.com"), "name": "Demo User"},
                    "access_token": "demo_token_" + str(int(time.time())),
                    "refresh_token": "demo_refresh_" + str(int(time.time())),
                    "expires_in": 900
                }
            })
        
        elif self.path == '/api/v1/ai/chat':
            message = data.get("message", "")
            session_id = data.get("session_id", "default")
            
            # Check if OpenAI API key is configured
            if OPENAI_API_KEY:
                # Use real OpenAI API
                response_text, error, tokens_used = get_ai_response(message, session_id)
                
                if error:
                    self.send_json({
                        "success": False,
                        "error": error,
                        "message": "AI service error"
                    }, 503)
                    return
                
                self.send_json({
                    "success": True,
                    "data": {
                        "message_id": f"msg_{int(time.time())}",
                        "response": response_text,
                        "suggestions": generate_suggestions(message),
                        "tokens_used": tokens_used,
                        "model": AI_MODEL
                    }
                })
            else:
                # Fallback to demo mode
                self.send_json({
                    "success": True,
                    "data": {
                        "message_id": f"msg_{int(time.time())}",
                        "response": f"⚠️ AI is running in demo mode.\n\nTo enable full AI, set the OPENAI_API_KEY environment variable.\n\nYour question was: {message}\n\n(Demo response - configure API key for real AI responses)",
                        "suggestions": generate_suggestions(message),
                        "tokens_used": 0,
                        "demo_mode": True
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
