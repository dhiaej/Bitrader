# PDF to Course System - Production Guide

## Overview

This system automatically converts PDF training files into complete e-learning courses with:
1. ✅ PDF text extraction
2. ✅ Automatic module splitting using AI
3. ✅ Narrated video generation for each module
4. ✅ Quiz generation after each module
5. ✅ Final exam generation
6. ✅ Progress tracking with quiz scores
7. ✅ Certificate generation upon completion

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install System Dependencies (for video generation)

**Windows:**
- Download ffmpeg from https://ffmpeg.org/download.html
- Add to PATH or place in project directory

**Linux/Mac:**
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg  # Mac
```

### 3. Environment Variables

Ensure your `.env` file has:
```env
GEMINI_API_KEY=your_gemini_api_key  # For AI content generation
# OR
GROQ_API_KEY=your_groq_api_key  # Fallback option
```

## API Endpoints

### Upload PDF and Create Course

**POST** `/api/formations/upload-pdf`

Upload a PDF file to automatically create a complete course.

**Request:**
- `file`: PDF file (multipart/form-data)
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
    "estimated_duration": 75
  },
  "modules_count": 5,
  "message": "Formation created successfully with 5 modules, quizzes, and final exam"
}
```

### Get Module Quiz

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

### Submit Quiz

**POST** `/api/formations/{formation_id}/modules/{module_id}/quiz/submit`

Submit quiz answers and get score.

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
  "attempt_id": 1
}
```

### Get Final Exam

**GET** `/api/formations/{formation_id}/exam`

Get final exam questions covering all modules.

### Submit Final Exam

**POST** `/api/formations/{formation_id}/exam/submit`

Submit exam answers. If passed (≥70%), automatically:
- Updates progress to COMPLETED
- Generates and saves certificate

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

### Get Certificate

**GET** `/api/formations/{formation_id}/certificate/{user_id}`

Get certificate URL for completed formation.

## Workflow

### For Admins (Creating Courses):

1. **Upload PDF**: Use `/api/formations/upload-pdf` endpoint
2. **System automatically**:
   - Extracts text from PDF
   - Splits into logical modules (using AI)
   - Generates videos for each module
   - Creates quizzes for each module
   - Generates final exam
3. **Course is ready** for students

### For Students (Taking Courses):

1. **Browse formations**: GET `/api/formations`
2. **Start formation**: Progress is tracked automatically
3. **Watch module videos**: Access via `video_url` in module
4. **Take module quiz**: GET quiz → Submit answers → Get score
5. **Complete all modules**: Progress tracked automatically
6. **Take final exam**: GET exam → Submit answers
7. **Receive certificate**: Automatically generated if exam passed (≥70%)

## Database Models

### New Models Added:

- **Module**: Represents a module within a formation
- **Quiz**: Quiz for a module (with questions JSON)
- **QuizAttempt**: User's quiz attempt with score
- **Exam**: Final exam for a formation
- **ExamAttempt**: User's exam attempt with score

### Updated Models:

- **Formation**: Now has relationships to modules and exam
- **UserProgress**: Tracks completion status
- **Certificate**: Generated PDF certificates

## Features

### PDF Processing
- Supports PyPDF2 and pdfplumber
- Extracts text and metadata
- Handles various PDF formats

### Module Splitting
- AI-powered intelligent splitting
- Falls back to paragraph-based splitting if AI unavailable
- Creates logical, self-contained modules

### Video Generation
- Text-to-speech narration (gTTS or pyttsx3)
- Video creation with ffmpeg
- Falls back to audio-only if video generation fails

### Quiz & Exam Generation
- AI-generated questions from content
- Multiple choice format
- Configurable passing scores
- Automatic scoring

### Certificate Generation
- Professional PDF certificates
- Includes user name, course title, completion date, score
- Generated using ReportLab

## Troubleshooting

### Video Generation Fails
- Ensure ffmpeg is installed and in PATH
- Check TTS library installation (gtts or pyttsx3)
- Videos will fall back to audio-only if video creation fails

### AI Content Generation Fails
- Check GEMINI_API_KEY or GROQ_API_KEY in .env
- System will use fallback methods (simple splitting, generic questions)

### PDF Extraction Fails
- Ensure PyPDF2 or pdfplumber is installed
- Some PDFs may be image-based (OCR would be needed)

## Production Considerations

1. **Video Storage**: Videos can be large. Consider cloud storage (S3, etc.)
2. **Background Processing**: For large PDFs, consider async task queues (Celery)
3. **Rate Limiting**: Add rate limiting for PDF uploads
4. **File Size Limits**: Set appropriate limits for PDF uploads
5. **Error Handling**: All services have fallback mechanisms
6. **Monitoring**: Add logging and monitoring for video generation jobs

## Testing

Test the system:

```bash
# 1. Start the backend
cd backend
python main.py

# 2. Upload a PDF (using curl or Postman)
curl -X POST "http://localhost:8000/api/formations/upload-pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@training.pdf" \
  -F "title=My Training Course" \
  -F "level=INTERMEDIATE"
```

## Next Steps

- Add video quality options
- Support for multiple languages
- Add video thumbnails
- Implement video streaming
- Add quiz question types (multiple select, true/false, etc.)
- Add certificate templates
- Implement course preview
- Add analytics and reporting

