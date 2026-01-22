"""
Quiz Generation Service
Service for generating quizzes from module content using AI
"""
import logging
from typing import List, Dict, Any, Optional
import json

from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class QuizGenerationService:
    """Service for generating quizzes from content"""
    
    async def generate_quiz_for_module(
        self,
        module_content: str,
        module_title: str,
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Generate quiz questions for a module
        
        Args:
            module_content: Content of the module
            module_title: Title of the module
            num_questions: Number of questions to generate
            
        Returns:
            Dictionary with questions array
        """
        prompt = f"""You are an expert educational content creator. Generate a quiz based on the following module content.

MODULE TITLE: {module_title}

MODULE CONTENT:
{module_content[:10000]}  # Limit content length

INSTRUCTIONS:
1. Create {num_questions} multiple-choice questions
2. Each question should test understanding of key concepts from the module
3. Questions should range from basic recall to application
4. Each question must have:
   - A clear, concise question text
   - 4 answer options (A, B, C, D)
   - Exactly one correct answer
   - A brief explanation for the correct answer

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "id": "q1",
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation of why this is correct"
    }},
    ...
  ]
}}

Respond ONLY with valid JSON. No markdown, no explanations, just the JSON object."""

        try:
            response = await gemini_service.generate_chat_response(
                prompt=prompt,
                context="You are creating educational quiz questions. Be accurate and educational."
            )
            
            # Extract JSON from response
            json_text = self._extract_json_from_response(response)
            result = json.loads(json_text)
            
            questions = result.get("questions", [])
            
            if not questions or len(questions) < 3:
                # Fallback: generate simple questions
                logger.warning("AI didn't generate enough questions, using fallback")
                questions = self._generate_fallback_questions(module_content, num_questions)
            
            # Validate questions
            validated_questions = []
            for q in questions:
                if self._validate_question(q):
                    validated_questions.append(q)
            
            if len(validated_questions) < 3:
                validated_questions = self._generate_fallback_questions(
                    module_content, num_questions
                )
            
            return {
                "questions": validated_questions[:num_questions],
                "passing_score": 70.0
            }
            
        except Exception as e:
            logger.error(f"Error generating quiz with AI: {e}")
            # Fallback
            return {
                "questions": self._generate_fallback_questions(module_content, num_questions),
                "passing_score": 70.0
            }
    
    async def generate_final_exam(
        self,
        all_modules_content: List[Dict[str, str]],
        formation_title: str,
        num_questions: int = 20
    ) -> Dict[str, Any]:
        """
        Generate final exam covering all modules
        
        Args:
            all_modules_content: List of dicts with 'title' and 'content' for each module
            formation_title: Title of the formation
            num_questions: Number of exam questions
            
        Returns:
            Dictionary with questions array
        """
        # Combine all module content
        combined_content = "\n\n".join([
            f"MODULE: {m.get('title', 'Module')}\n{m.get('content', '')[:5000]}"
            for m in all_modules_content
        ])
        
        prompt = f"""You are an expert educational content creator. Generate a comprehensive final exam based on the following course content.

COURSE TITLE: {formation_title}

COURSE CONTENT (All Modules):
{combined_content[:30000]}  # Limit content length

INSTRUCTIONS:
1. Create {num_questions} multiple-choice questions covering all modules
2. Questions should test comprehensive understanding across all topics
3. Mix question types: recall, application, analysis
4. Each question must have:
   - A clear, concise question text
   - 4 answer options (A, B, C, D)
   - Exactly one correct answer
   - A brief explanation for the correct answer
5. Ensure questions cover different modules proportionally

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "id": "q1",
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation of why this is correct",
      "module_reference": "Module title this question relates to"
    }},
    ...
  ]
}}

Respond ONLY with valid JSON. No markdown, no explanations, just the JSON object."""

        try:
            response = await gemini_service.generate_chat_response(
                prompt=prompt,
                context="You are creating a comprehensive final exam. Cover all topics thoroughly."
            )
            
            # Extract JSON from response
            json_text = self._extract_json_from_response(response)
            result = json.loads(json_text)
            
            questions = result.get("questions", [])
            
            if not questions or len(questions) < 10:
                # Fallback
                logger.warning("AI didn't generate enough exam questions, using fallback")
                questions = self._generate_fallback_exam_questions(
                    all_modules_content, num_questions
                )
            
            # Validate questions
            validated_questions = []
            for q in questions:
                if self._validate_question(q):
                    validated_questions.append(q)
            
            if len(validated_questions) < 10:
                validated_questions = self._generate_fallback_exam_questions(
                    all_modules_content, num_questions
                )
            
            return {
                "questions": validated_questions[:num_questions],
                "passing_score": 70.0
            }
            
        except Exception as e:
            logger.error(f"Error generating exam with AI: {e}")
            # Fallback
            return {
                "questions": self._generate_fallback_exam_questions(
                    all_modules_content, num_questions
                ),
                "passing_score": 70.0
            }
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from AI response"""
        response = response.strip()
        
        # Remove markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Find JSON object
        start_idx = response.find("{")
        end_idx = response.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return response[start_idx:end_idx + 1]
        
        return response
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate that a question has all required fields"""
        required = ["question", "options", "correct_answer"]
        if not all(key in question for key in required):
            return False
        
        options = question.get("options", {})
        if not isinstance(options, dict) or len(options) < 4:
            return False
        
        correct = question.get("correct_answer", "")
        if correct not in options:
            return False
        
        return True
    
    def _generate_fallback_questions(
        self,
        content: str,
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generate simple fallback questions"""
        questions = []
        
        # Simple approach: create generic questions
        for i in range(min(num_questions, 5)):
            questions.append({
                "id": f"q{i+1}",
                "question": f"Based on the module content, which statement is most accurate?",
                "options": {
                    "A": "The content covers important concepts",
                    "B": "The content is not relevant",
                    "C": "The content needs more detail",
                    "D": "The content is incomplete"
                },
                "correct_answer": "A",
                "explanation": "This is a placeholder question. Review the module content for accurate answers."
            })
        
        return questions
    
    def _generate_fallback_exam_questions(
        self,
        modules: List[Dict[str, str]],
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generate fallback exam questions"""
        questions = []
        
        questions_per_module = max(1, num_questions // len(modules)) if modules else num_questions
        
        for module_idx, module in enumerate(modules[:5]):  # Limit to 5 modules
            for i in range(questions_per_module):
                questions.append({
                    "id": f"q{len(questions)+1}",
                    "question": f"Which concept from {module.get('title', 'the module')} is most important?",
                    "options": {
                        "A": "Key concepts covered in the module",
                        "B": "Minor details",
                        "C": "Unrelated topics",
                        "D": "Incomplete information"
                    },
                    "correct_answer": "A",
                    "explanation": "This is a placeholder question. Review all modules for accurate answers.",
                    "module_reference": module.get("title", f"Module {module_idx + 1}")
                })
        
        return questions[:num_questions]


# Singleton instance
quiz_generation_service = QuizGenerationService()

