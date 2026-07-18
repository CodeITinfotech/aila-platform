import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { createClient } from 'redis';
import pkg from 'pg';
const { Pool } = pkg;

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://aila:aila_dev_password@localhost:5432/aila_dev',
});

// Redis connection
const redisClient = createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379'
});

redisClient.on('error', (err) => console.log('Redis Client Error', err));
redisClient.connect().then(() => console.log('Connected to Redis'));

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Check PostgreSQL
    const dbResult = await pool.query('SELECT NOW()');
    
    // Check Redis
    await redisClient.ping();
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'connected',
        redis: 'connected',
        uptime: process.uptime()
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// API info endpoint
app.get('/api/v1', (req, res) => {
  res.json({
    name: 'AILA Platform API',
    version: '1.0.0',
    description: 'AI Personalized Learning Platform',
    endpoints: {
      health: '/health',
      auth: '/api/v1/auth',
      users: '/api/v1/users',
      courses: '/api/v1/courses',
      lessons: '/api/v1/lessons',
      quizzes: '/api/v1/quizzes',
      ai: '/api/v1/ai',
      achievements: '/api/v1/achievements',
      leaderboard: '/api/v1/leaderboard'
    }
  });
});

// Auth endpoints
app.post('/api/v1/auth/register', async (req, res) => {
  try {
    const { email, password, name, role = 'student' } = req.body;
    
    if (!email || !password || !name) {
      return res.status(400).json({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: 'Missing required fields' }
      });
    }
    
    // Check if user exists
    const existing = await pool.query('SELECT id FROM users WHERE email = $1', [email]);
    if (existing.rows.length > 0) {
      return res.status(409).json({
        success: false,
        error: { code: 'CONFLICT', message: 'User already exists' }
      });
    }
    
    // Create user (password should be hashed in production)
    const result = await pool.query(
      `INSERT INTO users (email, password_hash, name, status) 
       VALUES ($1, $2, $3, 'pending') RETURNING id, email, name, status, created_at`,
      [email, password, name]
    );
    
    res.status(201).json({
      success: true,
      data: {
        user: result.rows[0],
        message: 'Registration successful. Please verify your email.'
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_ERROR', message: 'Registration failed' }
    });
  }
});

app.post('/api/v1/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: 'Missing credentials' }
      });
    }
    
    // Find user
    const result = await pool.query(
      'SELECT id, email, name, password_hash, status FROM users WHERE email = $1',
      [email]
    );
    
    if (result.rows.length === 0) {
      return res.status(401).json({
        success: false,
        error: { code: 'UNAUTHORIZED', message: 'Invalid credentials' }
      });
    }
    
    const user = result.rows[0];
    
    // Verify password (use bcrypt.compare in production)
    if (password !== user.password_hash) {
      return res.status(401).json({
        success: false,
        error: { code: 'UNAUTHORIZED', message: 'Invalid credentials' }
      });
    }
    
    // Check if user is active
    if (user.status !== 'active') {
      return res.status(403).json({
        success: false,
        error: { code: 'FORBIDDEN', message: 'Account not active' }
      });
    }
    
    // Generate tokens (use JWT in production)
    const accessToken = Buffer.from(`${user.id}:${Date.now()}`).toString('base64');
    const refreshToken = Buffer.from(`${user.id}:${Date.now()}:refresh`).toString('base64');
    
    // Store session in Redis
    await redisClient.setEx(`session:${user.id}`, 3600, JSON.stringify({ accessToken, refreshToken }));
    
    res.json({
      success: true,
      data: {
        user: { id: user.id, email: user.email, name: user.name },
        access_token: accessToken,
        refresh_token: refreshToken,
        expires_in: 900 // 15 minutes
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_ERROR', message: 'Login failed' }
    });
  }
});

// Courses endpoint (sample data)
app.get('/api/v1/courses', async (req, res) => {
  try {
    // Try to get from database
    let courses;
    try {
      const result = await pool.query(
        'SELECT id, title, description, price, difficulty, total_students FROM courses LIMIT 20'
      );
      courses = result.rows;
    } catch {
      // If table doesn't exist, return sample data
      courses = [
        { id: '1', title: 'Python Fundamentals', description: 'Learn Python from scratch', price: 0, difficulty: 'beginner', total_students: 15420 },
        { id: '2', title: 'Advanced JavaScript', description: 'Master modern JavaScript', price: 49.99, difficulty: 'advanced', total_students: 8950 },
        { id: '3', title: 'Data Science Basics', description: 'Introduction to Data Science', price: 0, difficulty: 'intermediate', total_students: 12300 }
      ];
    }
    
    res.json({
      success: true,
      data: courses,
      meta: { total: courses.length }
    });
  } catch (error) {
    console.error('Courses error:', error);
    res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch courses' }
    });
  }
});

// AI Tutor endpoint (mock)
app.post('/api/v1/ai/chat', async (req, res) => {
  try {
    const { message, context } = req.body;
    
    if (!message) {
      return res.status(400).json({
        success: false,
        error: { code: 'VALIDATION_ERROR', message: 'Message is required' }
      });
    }
    
    // Mock AI response (replace with actual AI integration)
    const responses = [
      "I'd be happy to help you with that! Let me explain the concept step by step.",
      "Great question! This topic is fundamental to understanding the subject.",
      "Let me break this down for you in a simple way.",
      "That's a common point of confusion. Here's how it works:",
      "Excellent! You're asking the right questions. Let me clarify."
    ];
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)];
    
    res.json({
      success: true,
      data: {
        message_id: `msg_${Date.now()}`,
        response: `${randomResponse}\n\n(This is a demo response. AI integration coming soon!)`,
        suggestions: [
          "Can you give me an example?",
          "How does this apply in practice?",
          "What are common mistakes to avoid?"
        ],
        tokens_used: Math.floor(Math.random() * 200) + 50
      }
    });
  } catch (error) {
    console.error('AI chat error:', error);
    res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_ERROR', message: 'AI service unavailable' }
    });
  }
});

// Leaderboard endpoint (mock)
app.get('/api/v1/leaderboard', async (req, res) => {
  const mockLeaderboard = [
    { rank: 1, name: 'Alex Chen', xp_total: 25000, level: 65, streak: 45 },
    { rank: 2, name: 'Maria Garcia', xp_total: 23500, level: 62, streak: 38 },
    { rank: 3, name: 'James Wilson', xp_total: 22000, level: 58, streak: 30 },
    { rank: 4, name: 'Priya Sharma', xp_total: 21000, level: 55, streak: 28 },
    { rank: 5, name: 'David Kim', xp_total: 19500, level: 52, streak: 22 }
  ];
  
  res.json({
    success: true,
    data: mockLeaderboard,
    meta: { total_participants: 15420 }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: { code: 'NOT_FOUND', message: 'Endpoint not found' }
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    success: false,
    error: { code: 'INTERNAL_ERROR', message: 'Internal server error' }
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`
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
║    API Server v1.0.0                                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

🚀 Server running on port ${PORT}
📖 API Documentation: http://localhost:${PORT}/api/v1
💚 Health Check: http://localhost:${PORT}/health
`);
});

export default app;
