# Production-Ready PDF to Course System - Complete Guide

## 🎯 System Overview

This production-ready system automatically converts PDF training files into complete e-learning courses with:

1. ✅ **PDF Upload & Text Extraction** - Accepts PDF files and extracts text content
2. ✅ **Automatic Module Splitting** - Intelligently splits PDF into logical modules using AI
3. ✅ **Narrated Video Generation** - Converts each module into a narrated video with TTS
4. ✅ **Module Quizzes** - Creates quizzes after each module with AI-generated questions
5. ✅ **Final Exam** - Generates comprehensive final exam covering all modules
6. ✅ **Progress Tracking** - Tracks user progress, quiz scores, and module completion
7. ✅ **Certificate Generation** - Automatically issues PDF certificates upon completion

## 📋 API Endpoints

### 1. Upload PDF and Create Course

**POST** `/api/formations/upload-pdf`

Upload a PDF file to automatically create a complete course.

**Request:**
- `file`: PDF file (multipart/form-data, required)
- `title`: Optional course title (extracted from PDF if not provided)
- `description`: Optional description
- `level`: Course level (BEGINNER, INTERMEDIATE, ADVANCED) - default: INTERMEDIATE

**Response:**
```json
{
  "formation": {
    "id": 1,
    "title": "Course Title",
    "description": "...",
    "level": "INTERMEDIATE",
    "content_json": [...],
    "estimated_duration": 75,
    "has_modules": true,
    "modules_count": 5,
    "has_exam": true
  },
  "modules_count": 5,
  "message": "Formation created successfully with 5 modules, quizzes, and final exam"
}
```

### 2. Get Formation Details

**GET** `/api/formations/{formation_id}`

Get formation details with optional user-specific progress and certificate info.

**Response (for authenticated user):**
```json
{
  "id": 1,
  "title": "Course Title",
  "description": "...",
  "level": "INTERMEDIATE",
  "content_json": [...],
  "has_modules": true,
  "modules_count": 5,
  "has_exam": true,
  "user_progress": {
    "status": "IN_PROGRESS",
    "progress_percentage": 60.0,
    "started_at": "2024-01-01T00:00:00",
    "completed_at": null
  },
  "certificate": {
    "certificate_url": "/certificates/1_1_1234567890.pdf",
    "issued_at": "2024-01-15T00:00:00"
  }
}
```

### 3. Get Module Details

**GET** `/api/formations/{formation_id}/modules/{module_id}`

Get detailed module information including video and quiz status.

**Response:**
```json
{
  "id": 1,
  "formation_id": 1,
  "module_number": 1,
  "title": "Module 1: Introduction",
  "content": "Module content text...",
  "video_url": "/videos/formation_1_module_1.mp4",
  "video_duration": 900,
  "quiz": {
    "quiz_id": 1,
    "questions_count": 5,
    "passing_score": 70.0,
    "has_attempted": true,
    "best_score": 80.0,
    "passed": true
  },
  "created_at": "2024-01-01T00:00:00"
}
```

### 4. Mark Module as Completed

**POST** `/api/formations/{formation_id}/modules/{module_id}/complete`

Mark a module as watched/completed (for video viewing).

**Response:**
```json
{
  "module_id": 1,
  "completed": true,
  "progress_percentage": 20.0,
  "total_modules": 5,
  "completed_modules": 1
}
```

### 5. Get Module Quiz

**GET** `/api/formations/{formation_id}/modules/{module_id}/quiz`

Get quiz questions for a specific module.

**Response:**
```json
{
  "quiz_id": 1,
  "module_id": 1,
  "questions": [
    {
      "id": "q1",
      "question": "What is...?",
      "options": {
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      },
      "correct_answer": "A",
      "explanation": "..."
    }
  ],
  "passing_score": 70.0
}
```

### 6. Submit Quiz

**POST** `/api/formations/{formation_id}/modules/{module_id}/quiz/submit`

Submit quiz answers. Automatically updates progress if passed.

**Request:**
```json
{
  "q1": "A",
  "q2": "B",
  ...
}
```

**Response:**
```json
{
  "score": 80.0,
  "passed": true,
  "correct": 4,
  "total": 5,
  "passing_score": 70.0,
  "attempt_id": 1,
  "progress_updated": true
}
```

### 7. Get Final Exam

**GET** `/api/formations/{formation_id}/exam`

Get final exam questions covering all modules.

**Response:**
```json
{
  "exam_id": 1,
  "formation_id": 1,
  "questions": [...],
  "passing_score": 70.0
}
```

### 8. Submit Final Exam

**POST** `/api/formations/{formation_id}/exam/submit`

Submit exam answers. If passed (≥70%), automatically:
- Updates progress to COMPLETED
- Generates and saves certificate

**Request:**
```json
{
  "q1": "A",
  "q2": "B",
  ...
}
```

**Response:**
```json
{
  "score": 85.0,
  "passed": true,
  "correct": 17,
  "total": 20,
  "passing_score": 70.0,
  "attempt_id": 1,
  "certificate_generated": true
}
```

### 9. Get Detailed Progress

**GET** `/api/formations/{formation_id}/progress/{user_id}/detailed`

Get detailed progress with module and quiz completion status.

**Response:**
```json
{
  "formation_id": 1,
  "formation_title": "Course Title",
  "user_id": 1,
  "status": "IN_PROGRESS",
  "progress_percentage": 60.0,
  "started_at": "2024-01-01T00:00:00",
  "completed_at": null,
  "modules": [
    {
      "id": 1,
      "module_number": 1,
      "title": "Module 1",
      "video_url": "/videos/...",
      "video_duration": 900,
      "is_completed": true,
      "quiz": {
        "has_quiz": true,
        "has_attempted": true,
        "passed": true,
        "score": 80.0,
        "passing_score": 70.0
      }
    }
  ],
  "total_modules": 5,
  "completed_modules": 3,
  "exam": {
    "exam_id": 1,
    "has_attempted": false,
    "passed": false,
    "score": null,
    "passing_score": 70.0
  },
  "has_certificate": false,
  "certificate_url": null
}
```

### 10. Get User Certificates

**GET** `/api/formations/certificates/{user_id}`

Get all certificates for a user.

**Response:**
```json
{
  "certificates": [
    {
      "id": 1,
      "formation_id": 1,
      "formation_title": "Course Title",
      "certificate_url": "/certificates/1_1_1234567890.pdf",
      "issued_at": "2024-01-15T00:00:00"
    }
  ]
}
```

### 11. Get Certificate

**GET** `/api/formations/{formation_id}/certificate/{user_id}`

Get certificate URL for a completed formation.

**Response:**
```json
{
  "certificate_url": "/certificates/1_1_1234567890.pdf",
  "issued_at": "2024-01-15T00:00:00"
}
```

## 🔄 Complete Workflow

### For Admins (Creating Courses):

1. **Upload PDF**: `POST /api/formations/upload-pdf`
   - System automatically:
     - Extracts text from PDF
     - Splits into logical modules (using AI)
     - Generates videos for each module
     - Creates quizzes for each module
     - Generates final exam
2. **Course is ready** for students

### For Students (Taking Courses):

1. **Browse formations**: `GET /api/formations`
2. **View formation details**: `GET /api/formations/{formation_id}`
   - See progress, modules, and certificate if completed
3. **Watch module video**: `GET /api/formations/{formation_id}/modules/{module_id}`
   - Access video URL
4. **Mark module as completed**: `POST /api/formations/{formation_id}/modules/{module_id}/complete`
5. **Take module quiz**: 
   - `GET /api/formations/{formation_id}/modules/{module_id}/quiz`
   - `POST /api/formations/{formation_id}/modules/{module_id}/quiz/submit`
   - Progress automatically updated if passed
6. **Complete all modules**: Progress tracked automatically
7. **Take final exam**: 
   - `GET /api/formations/{formation_id}/exam`
   - `POST /api/formations/{formation_id}/exam/submit`
8. **Receive certificate**: Automatically generated if exam passed (≥70%)
   - Certificate URL available in formation details
   - View all certificates: `GET /api/formations/certificates/{user_id}`

## 🎯 Key Features

### Automatic Progress Tracking

- Progress is automatically updated when:
  - Module is marked as completed
  - Quiz is passed (≥70%)
  - Final exam is passed (≥70%)
- Progress percentage calculated based on completed modules
- Status: NOT_STARTED → IN_PROGRESS → COMPLETED

### Certificate Generation

- Automatically generated when final exam is passed
- Includes:
  - User name
  - Formation title
  - Completion date
  - Final exam score
- PDF format, downloadable
- Available in formation details and certificate listing

### Quiz & Exam System

- **Module Quizzes**: 5 questions per module, 70% passing score
- **Final Exam**: 20 questions covering all modules, 70% passing score
- All attempts are saved with scores
- Best scores tracked for each quiz/exam

## 📦 Dependencies

All required packages are in `requirements.txt`:

- **PDF Processing**: PyPDF2, pdfplumber
- **Video Generation**: gtts, pyttsx3, ffmpeg (system dependency)
- **Certificate Generation**: reportlab, Pillow
- **AI Content Generation**: google-generativeai (or groq as fallback)

## 🚀 Setup Instructions

1. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Install system dependencies** (for video generation):
   - **Windows**: Download ffmpeg from https://ffmpeg.org/download.html
   - **Linux**: `sudo apt-get install ffmpeg`
   - **Mac**: `brew install ffmpeg`

3. **Configure environment variables** (`.env`):
   ```env
   GEMINI_API_KEY=your_gemini_api_key  # For AI content generation
   # OR
   GROQ_API_KEY=your_groq_api_key  # Fallback option
   ```

4. **Start the backend**:
   ```bash
   python main.py
   ```

## ✅ Production Checklist

- [x] PDF text extraction with fallback methods
- [x] AI-powered module splitting with fallback
- [x] Video generation with TTS (gTTS/pyttsx3)
- [x] Quiz generation for each module
- [x] Final exam generation
- [x] Automatic progress tracking
- [x] Certificate generation on completion
- [x] Comprehensive API endpoints
- [x] Error handling and fallbacks
- [x] User authentication and authorization
- [x] Detailed progress tracking
- [x] Certificate listing and access

## 🎉 System is Production-Ready!

The system is fully functional and ready for production use. All features are implemented with proper error handling, fallbacks, and comprehensive API endpoints.

