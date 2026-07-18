# AILA Platform API Documentation

## Overview

The AILA Platform provides a comprehensive REST API for all client applications. This document covers authentication, endpoints, request/response formats, and error handling.

## Base Configuration

| Environment | Base URL |
|-------------|----------|
| Production | `https://api.aila-learning.com/v1` |
| Staging | `https://api-staging.aila-learning.com/v1` |
| Development | `http://localhost:3001/v1` |

## Authentication

### Bearer Token

All API requests require authentication using a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | User registration |
| POST | `/auth/login` | Email/password login |
| POST | `/auth/logout` | Logout (invalidate session) |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| POST | `/auth/verify-email` | Verify email address |
| POST | `/auth/oauth/google` | Google OAuth login |
| POST | `/auth/oauth/apple` | Apple OAuth login |
| POST | `/auth/otp/send` | Send OTP code |
| POST | `/auth/otp/verify` | Verify OTP code |

### Authentication Examples

#### Register

```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "SecurePass123!",
  "name": "John Student",
  "role": "student"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "student@example.com",
      "name": "John Student",
      "status": "pending"
    },
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG..."
  }
}
```

#### Login

```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

## Rate Limiting

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 60 | 10 |
| Premium | 300 | 50 |
| Enterprise | 1000 | 200 |

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

## User APIs

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get current user profile |
| PUT | `/users/me` | Update profile |
| PUT | `/users/me/password` | Change password |
| PUT | `/users/me/avatar` | Upload avatar |
| DELETE | `/users/me` | Delete account |
| GET | `/users/me/progress` | Get learning progress |
| GET | `/users/me/achievements` | Get achievements |
| GET | `/users/me/stats` | Get user statistics |

### Get Current User

```http
GET /v1/users/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "student@example.com",
    "name": "John Student",
    "avatar_url": "https://cdn.aila.../avatar.jpg",
    "role": "student",
    "xp_total": 1250,
    "level": 12,
    "current_streak": 7,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Course APIs

### Course Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses` | List courses |
| GET | `/courses/:id` | Get course details |
| POST | `/courses` | Create course (teacher) |
| PUT | `/courses/:id` | Update course |
| DELETE | `/courses/:id` | Delete course |
| POST | `/courses/:id/enroll` | Enroll in course |
| DELETE | `/courses/:id/enroll` | Unenroll from course |
| GET | `/courses/:id/lessons` | Get course lessons |
| GET | `/courses/:id/progress` | Get course progress |
| POST | `/courses/:id/reviews` | Add review |

### List Courses

```http
GET /v1/courses?category=programming&difficulty=beginner&page=1&limit=20
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter by category slug |
| difficulty | string | beginner, intermediate, advanced |
| search | string | Search in title/description |
| sort | string | newest, popular, rating |
| page | number | Page number |
| limit | number | Items per page (max 50) |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Python Fundamentals",
      "slug": "python-fundamentals",
      "description": "Learn Python from scratch...",
      "thumbnail_url": "https://cdn.../thumb.jpg",
      "price": 0,
      "difficulty": "beginner",
      "total_students": 15420,
      "average_rating": 4.8,
      "total_lessons": 45,
      "total_duration_minutes": 1200,
      "teacher": {
        "id": "uuid",
        "name": "Jane Teacher"
      }
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Enroll in Course

```http
POST /v1/courses/:id/enroll
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "enrollment_id": "uuid",
    "course_id": "uuid",
    "status": "active",
    "started_at": "2024-06-15T10:30:00Z",
    "progress_percentage": 0
  }
}
```

## Lesson APIs

### Lesson Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/lessons/:id` | Get lesson details |
| POST | `/lessons/:id/progress` | Update progress |
| POST | `/lessons/:id/complete` | Mark as complete |
| POST | `/lessons/:id/bookmark` | Add bookmark |
| DELETE | `/lessons/:id/bookmark` | Remove bookmark |
| GET | `/lessons/:id/download` | Get download URL |

### Update Lesson Progress

```http
POST /v1/lessons/:id/progress
Authorization: Bearer <token>
Content-Type: application/json

{
  "progress_seconds": 180,
  "video_position_seconds": 180
}
```

## Quiz APIs

### Quiz Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/quizzes/:id` | Get quiz details |
| POST | `/quizzes/:id/start` | Start quiz attempt |
| POST | `/quizzes/:id/submit` | Submit quiz answers |
| GET | `/quizzes/:id/attempts` | Get attempt history |
| GET | `/quizzes/:id/attempts/:attempt_id` | Get attempt details |
| GET | `/quizzes/:id/leaderboard` | Get quiz leaderboard |

### Start Quiz Attempt

```http
POST /v1/quizzes/:id/start
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "attempt_id": "uuid",
    "quiz_id": "uuid",
    "questions": [
      {
        "id": "uuid",
        "type": "mcq",
        "question_text": "What is Python?",
        "options": [
          { "id": "a", "text": "A snake" },
          { "id": "b", "text": "A programming language" },
          { "id": "c", "text": "A game" }
        ],
        "points": 1
      }
    ],
    "time_limit_minutes": 30,
    "started_at": "2024-06-15T10:30:00Z",
    "expires_at": "2024-06-15T11:00:00Z"
  }
}
```

### Submit Quiz Answers

```http
POST /v1/quizzes/:id/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "attempt_id": "uuid",
  "answers": [
    { "question_id": "uuid", "answer": "b" },
    { "question_id": "uuid", "answer": "a" }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "attempt_id": "uuid",
    "score": 85.0,
    "total_points": 20,
    "earned_points": 17,
    "correct_count": 17,
    "incorrect_count": 3,
    "passed": true,
    "completed_at": "2024-06-15T10:45:00Z",
    "time_taken_seconds": 900,
    "review": [
      {
        "question_id": "uuid",
        "is_correct": true,
        "explanation": "Python is a programming language..."
      }
    ]
  }
}
```

## AI Tutor APIs

### AI Tutor Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/chat` | Send chat message |
| POST | `/ai/voice` | Process voice input |
| POST | `/ai/analyze-image` | Analyze uploaded image |
| GET | `/ai/history` | Get conversation history |
| GET | `/ai/conversations/:id` | Get conversation details |
| POST | `/ai/flashcards` | Generate flashcards |
| POST | `/ai/quiz` | Generate quiz |
| POST | `/ai/explain` | Explain concept |

### Send Chat Message

```http
POST /v1/ai/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Can you explain what a variable is in Python?",
  "context": {
    "lesson_id": "uuid",
    "course_id": "uuid"
  },
  "language": "en"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message_id": "uuid",
    "response": "A variable in Python is like a container that stores data...",
    "suggestions": [
      "Show me an example",
      "How do I name variables?",
      "What are data types?"
    ],
    "tokens_used": 150
  }
}
```

### Generate Flashcards

```http
POST /v1/ai/flashcards
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic": "Python Variables",
  "count": 10,
  "difficulty": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "flashcards": [
      {
        "front": "What is a variable?",
        "back": "A named storage location in memory that holds a value.",
        "hint": "Think of it as a labeled box"
      }
    ],
    "estimated_time_minutes": 15
  }
}
```

## Achievement & Gamification APIs

### Achievement Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/achievements` | List all achievements |
| GET | `/users/me/achievements` | Get user's achievements |
| GET | `/leaderboard` | Get global leaderboard |
| GET | `/leaderboard/course/:id` | Get course leaderboard |
| GET | `/users/me/xp-history` | Get XP transaction history |

### Get Leaderboard

```http
GET /v1/leaderboard?scope=global&period=weekly&limit=50
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "user_id": "uuid",
      "name": "Top Student",
      "avatar_url": "https://...",
      "xp_total": 15000,
      "level": 45,
      "is_current_user": false
    },
    {
      "rank": 42,
      "user_id": "current-user-uuid",
      "name": "You",
      "avatar_url": "https://...",
      "xp_total": 1250,
      "level": 12,
      "is_current_user": true
    }
  ],
  "meta": {
    "user_rank": 42,
    "total_participants": 5000
  }
}
```

## Notification APIs

### Notification Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications` | List notifications |
| PUT | `/notifications/:id/read` | Mark as read |
| PUT | `/notifications/read-all` | Mark all as read |
| DELETE | `/notifications/:id` | Delete notification |
| PUT | `/users/me/notification-settings` | Update settings |

### Update Notification Settings

```http
PUT /v1/users/me/notification-settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "push_enabled": true,
  "email_enabled": true,
  "categories": {
    "achievements": true,
    "streak_reminders": true,
    "course_updates": false,
    "marketing": false
  }
}
```

## Payment APIs

### Payment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/subscriptions/plans` | List subscription plans |
| POST | `/subscriptions` | Create subscription |
| GET | `/subscriptions/current` | Get current subscription |
| PUT | `/subscriptions/cancel` | Cancel subscription |
| POST | `/payments/initiate` | Initiate payment |
| GET | `/payments/history` | Payment history |
| POST | `/coupons/validate` | Validate coupon |

### Create Subscription

```http
POST /v1/subscriptions
Authorization: Bearer <token>
Content-Type: application/json

{
  "plan_id": "plan_premium_monthly",
  "payment_method_id": "pm_card_visa"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid input data |
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

## Webhooks

### Supported Webhooks

| Event | Description |
|-------|-------------|
| `user.registered` | New user registration |
| `user.deleted` | User account deleted |
| `subscription.created` | New subscription |
| `subscription.cancelled` | Subscription cancelled |
| `payment.completed` | Payment successful |
| `payment.failed` | Payment failed |
| `course.enrolled` | User enrolled in course |
| `course.completed` | Course completed |
| `certificate.issued` | Certificate issued |

### Webhook Payload

```json
{
  "event": "subscription.created",
  "timestamp": "2024-06-15T10:30:00Z",
  "data": {
    "subscription_id": "uuid",
    "user_id": "uuid",
    "plan_id": "plan_premium_monthly",
    "status": "active"
  },
  "signature": "sha256=..."
}
```

---

*API Version: 1.0*
*Last Updated: 2026-07-18*
