#!/usr/bin/env python3
"""
External Deployment Server for AILA Platform
Serves both static files and API on specified ports
"""

import os
import sys
import json
import time
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import threading

# Configuration
WEB_PORT = 12000
API_PORT = 12001

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

AI_RESPONSES = [
    "I'd be happy to help you with that! Let me explain the concept step by step.",
    "Great question! This topic is fundamental to understanding the subject.",
    "Let me break this down for you in a simple way.",
    "That's a common point of confusion. Here's how it works:",
    "Excellent! You're asking the right questions. Let me clarify."
]

class APIHandler(SimpleHTTPRequestHandler):
    """Handler for API requests"""
    
    def log_message(self, format, *args):
        print(f"[API] {args[0]}")
    
    def send_json(self, data, status=200):
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
            response = random.choice(AI_RESPONSES)
            self.send_json({
                "success": True,
                "data": {
                    "message_id": f"msg_{int(time.time())}",
                    "response": f"{response}\n\nYour question was: {message[:50]}...\n\n(This is a demo response. Full AI integration coming soon!)",
                    "suggestions": [
                        "Can you give me an example?",
                        "How does this apply in practice?",
                        "What are common mistakes to avoid?"
                    ],
                    "tokens_used": random.randint(50, 200)
                }
            })
        
        else:
            self.send_json({"error": "Not found", "code": "NOT_FOUND"}, 404)


class WebHandler(SimpleHTTPRequestHandler):
    """Handler for static web files"""
    
    def log_message(self, format, *args):
        print(f"[Web] {args[0]}")
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if self.path == '/' or self.path == '/index.html':
            self.serve_file('/workspace/project/apps/web/src/index.html')
        elif self.path == '/api':
            # Proxy to API
            self.send_response(302)
            self.send_header('Location', f'http://localhost:{API_PORT}/api/v1')
            self.end_headers()
        elif self.path.startswith('/api/'):
            # Proxy to API
            self.send_response(302)
            self.send_header('Location', f'http://localhost:{API_PORT}{self.path}')
            self.end_headers()
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Web Server Running - Port {WEB_PORT}".encode())
        else:
            # Try to serve static file
            file_path = '/workspace/project/apps/web/src' + self.path
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.serve_file(file_path)
            else:
                # Fallback to index.html
                self.serve_file('/workspace/project/apps/web/src/index.html')
    
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
