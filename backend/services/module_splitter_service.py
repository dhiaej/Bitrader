"""
Module Splitter Service
Service for intelligently splitting PDF content into logical modules using AI
"""
import logging
from typing import List, Dict, Any, Optional
import json

from services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class ModuleSplitterService:
    """Service for splitting PDF content into logical modules"""
    
    async def split_into_modules(
        self,
        pdf_text: str,
        title: Optional[str] = None,
        target_modules: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Split PDF text into logical modules using AI
        
        Args:
            pdf_text: Full text content from PDF
            title: Optional title of the course
            target_modules: Target number of modules (AI will adjust if needed)
            
        Returns:
            List of module dictionaries with title, content, and summary
        """
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise ValueError("PDF text is too short or empty")
        
        # Prepare prompt for AI
        prompt = f"""You are an expert educational content organizer. Your task is to split a training document into logical, well-structured modules.

DOCUMENT TITLE: {title or "Training Document"}

DOCUMENT CONTENT:
{pdf_text[:50000]}  # Limit to 50k chars to avoid token limits

INSTRUCTIONS:
1. Analyze the content and identify natural breakpoints (topics, chapters, concepts)
2. Split the content into approximately {target_modules} modules (adjust if content structure requires it)
3. Each module should:
   - Have a clear, descriptive title
   - Be self-contained but build on previous modules
   - Be roughly equal in length (aim for 1000-2000 words per module)
   - Cover a complete topic or concept
4. Ensure modules flow logically from basic to advanced concepts

OUTPUT FORMAT (JSON):
{{
  "modules": [
    {{
      "module_number": 1,
      "title": "Module Title",
      "content": "Full text content for this module...",
      "summary": "Brief summary of what this module covers"
    }},
    ...
  ],
  "total_modules": <number>
}}

Respond ONLY with valid JSON. No markdown, no explanations, just the JSON object."""

        try:
            # Use Gemini service to split content
            response = await gemini_service.generate_chat_response(
                prompt=prompt,
                context="You are splitting educational content into modules. Be precise and logical."
            )
            
            # Try to extract JSON from response
            json_text = self._extract_json_from_response(response)
            result = json.loads(json_text)
            
            modules = result.get("modules", [])
            
            if not modules:
                # Fallback: simple split by paragraphs
                logger.warning("AI didn't return modules, using fallback split")
                modules = self._fallback_split(pdf_text, target_modules)
            
            # Validate and clean modules
            validated_modules = []
            for module in modules:
                if module.get("content") and len(module["content"].strip()) > 50:
                    validated_modules.append({
                        "module_number": module.get("module_number", len(validated_modules) + 1),
                        "title": module.get("title", f"Module {len(validated_modules) + 1}"),
                        "content": module.get("content", "").strip(),
                        "summary": module.get("summary", "").strip()
                    })
            
            if not validated_modules:
                raise ValueError("Failed to create any valid modules")
            
            logger.info(f"Successfully split content into {len(validated_modules)} modules")
            return validated_modules
            
        except Exception as e:
            logger.error(f"Error splitting modules with AI: {e}")
            # Fallback to simple split
            logger.info("Using fallback module splitting")
            return self._fallback_split(pdf_text, target_modules)
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from AI response (may have markdown or extra text)"""
        # Try to find JSON in the response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Try to find JSON object
        start_idx = response.find("{")
        end_idx = response.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return response[start_idx:end_idx + 1]
        
        return response
    
    def _fallback_split(self, text: str, target_modules: int) -> List[Dict[str, Any]]:
        """
        Fallback method: simple paragraph-based splitting
        
        Args:
            text: Full text content
            target_modules: Target number of modules
            
        Returns:
            List of module dictionaries
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        if not paragraphs:
            # Split by single newlines
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        
        if not paragraphs:
            # Last resort: split by sentences
            import re
            sentences = re.split(r'[.!?]+\s+', text)
            paragraphs = [s.strip() for s in sentences if s.strip()]
        
        # Calculate paragraphs per module
        total_paragraphs = len(paragraphs)
        if total_paragraphs == 0:
            return [{
                "module_number": 1,
                "title": "Module 1",
                "content": text,
                "summary": "Training content"
            }]
        
        paragraphs_per_module = max(1, total_paragraphs // target_modules)
        
        modules = []
        current_module_paragraphs = []
        module_num = 1
        
        for i, para in enumerate(paragraphs):
            current_module_paragraphs.append(para)
            
            # Create module when we reach target size or at end
            if (len(current_module_paragraphs) >= paragraphs_per_module and 
                module_num < target_modules) or i == len(paragraphs) - 1:
                
                content = "\n\n".join(current_module_paragraphs)
                
                # Extract title from first sentence or paragraph
                title = f"Module {module_num}"
                if current_module_paragraphs:
                    first_para = current_module_paragraphs[0]
                    # Try to use first sentence as title (max 60 chars)
                    first_sentence = first_para.split('.')[0][:60]
                    if len(first_sentence) > 10:
                        title = first_sentence.strip()
                
                modules.append({
                    "module_number": module_num,
                    "title": title,
                    "content": content,
                    "summary": f"Module {module_num} content covering key concepts"
                })
                
                current_module_paragraphs = []
                module_num += 1
        
        return modules


# Singleton instance
module_splitter_service = ModuleSplitterService()

