# AILA Platform Database Design

## Overview

This document details the complete database architecture for the AILA AI Personalized Learning Platform. The database is designed to support high-performance, scalable operations with PostgreSQL as the primary database.

## Entity Relationships

### Core Entities

```
Users ─── UserRoles ─── Roles ─── Permissions
  │
  ├── StudentProfiles ─── Enrollments ─── LessonProgress
  │                        │
  │                        └── QuizAttempts ─── Questions
  │
  ├── TeacherProfiles ─── Courses ─── Modules ─── Lessons
  │
  ├── ParentProfiles ─── ParentChildLinks ─── (linked Students)
  │
  ├── Certificates
  ├── Achievements ─── BadgeAchievements
  ├── XPTransactions
  ├── Bookmarks
  ├── AIConversations ─── AIMessages
  └── StudyPlans ─── StudyPlanItems
```

## Table Definitions

### Core Tables (40 tables)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| users | User accounts | id, email, password_hash, name, status |
| roles | System roles | id, name, description |
| permissions | Access permissions | id, resource, action |
| user_roles | User-role assignments | user_id, role_id |
| sessions | Active sessions | user_id, token_hash, expires_at |
| student_profiles | Student-specific data | user_id, xp_total, current_streak |
| teacher_profiles | Teacher-specific data | user_id, bio, expertise |
| parent_profiles | Parent-specific data | user_id, occupation |
| categories | Course categories | id, name, parent_id |
| courses | Course information | id, teacher_id, title, price |
| modules | Course modules | id, course_id, title |
| lessons | Individual lessons | id, module_id, type, content_url |
| quizzes | Quiz assessments | id, lesson_id, time_limit |
| questions | Quiz questions | id, quiz_id, type, options |
| enrollments | Course enrollments | user_id, course_id, status |
| lesson_progress | Lesson completion | user_id, lesson_id, status |
| quiz_attempts | Quiz attempts | user_id, quiz_id, score |
| question_attempts | Question responses | quiz_attempt_id, question_id |
| achievements | Achievement definitions | id, name, category, tier |
| badge_achievements | Earned badges | user_id, achievement_id |
| xp_transactions | XP history | user_id, amount, type |
| certificates | Course certificates | user_id, course_id, verification_code |
| bookmarks | User bookmarks | user_id, lesson_id |
| downloads | Download history | user_id, lesson_id |
| notifications | User notifications | user_id, type, is_read |
| subscriptions | Premium subscriptions | user_id, plan_name, status |
| payments | Payment records | user_id, amount, status |
| coupons | Discount coupons | code, type, value |
| coupons_used | Coupon usage | coupon_id, user_id |
| ai_conversations | AI chat sessions | user_id, subject |
| ai_messages | AI chat messages | conversation_id, role, content |
| parent_child_links | Parent-child relationships | parent_id, child_id |
| study_plans | Personalized study plans | user_id, title |
| study_plan_items | Study plan items | study_plan_id, lesson_id |
| audit_logs | System audit trail | user_id, action, resource_type |
| support_tickets | Support requests | user_id, subject, status |
| ticket_messages | Support ticket messages | ticket_id, sender_id |
| reports | User reports | reporter_id, reason |
| reviews | Course reviews | user_id, course_id, rating |
| leaderboard_snapshots | XP snapshots | user_id, scope, rank |

## Key Indexes

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Course queries
CREATE INDEX idx_courses_teacher ON courses(teacher_id);
CREATE INDEX idx_courses_category ON courses(category_id);
CREATE INDEX idx_courses_fts ON courses USING gin(to_tsvector('english', title || ' ' || description));

-- Progress tracking
CREATE INDEX idx_progress_user_lesson ON lesson_progress(user_id, lesson_id);
CREATE INDEX idx_progress_enrollment ON lesson_progress(enrollment_id);

-- Quiz performance
CREATE INDEX idx_quiz_attempts_user_quiz ON quiz_attempts(user_id, quiz_id);

-- XP and gamification
CREATE INDEX idx_xp_transactions_user_date ON xp_transactions(user_id, created_at DESC);
CREATE INDEX idx_badge_achievements_user ON badge_achievements(user_id, earned_at DESC);
```

## Sample Queries

### Get Student Progress

```sql
SELECT 
    u.name,
    c.title as course,
    COUNT(lp.id) FILTER (WHERE lp.status = 'completed') as completed_lessons,
    COUNT(l.id) as total_lessons,
    e.progress_percentage
FROM users u
JOIN student_profiles sp ON u.id = sp.user_id
JOIN enrollments e ON u.id = e.user_id
JOIN courses c ON e.course_id = c.id
JOIN modules m ON c.id = m.course_id
JOIN lessons l ON m.id = l.module_id
LEFT JOIN lesson_progress lp ON l.id = lp.lesson_id AND u.id = lp.user_id
WHERE u.id = $1
GROUP BY u.name, c.title, e.progress_percentage;
```

### Get Leaderboard

```sql
SELECT 
    ROW_NUMBER() OVER (ORDER BY xp_total DESC) as rank,
    u.name,
    sp.xp_total,
    sp.current_streak
FROM users u
JOIN student_profiles sp ON u.id = sp.user_id
ORDER BY sp.xp_total DESC
LIMIT 100;
```

## Migrations

### Commands

```bash
npm run db:migrate           # Run pending migrations
npm run db:migrate:create    # Create new migration
npm run db:migrate:rollback  # Rollback last migration
```

---

*Document Version: 1.0*
