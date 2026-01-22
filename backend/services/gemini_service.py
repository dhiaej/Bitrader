"""
Gemini AI Service
Service for generating chat responses and course content.
Includes "Simulation Mode" to prevent crashes when API keys are invalid.
"""
from typing import Optional, Dict, Any
import logging
import json
import re
import random
from config import settings

logger = logging.getLogger(__name__)

# Try imports
try:
    import json5
    JSON5_AVAILABLE = True
except ImportError:
    JSON5_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GeminiService:
    """Service for Gemini AI integration with robust fallback"""
    
    def __init__(self):
        self.client = None
        self.openai_client = None
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.groq_key = getattr(settings, 'GROQ_API_KEY', '')
        
        # 1. Initialize OpenAI (Primary)
        openai_key = getattr(settings, 'OPENAI_API_KEY', '')
        if OPENAI_AVAILABLE and openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI init failed: {e}")

        # 2. Initialize Gemini (Secondary)
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("✅ Gemini client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Gemini init failed: {e}")

    def _get_mock_course(self, symbol: str) -> Dict[str, Any]:
        """Returns fake data so the app doesn't crash when APIs fail"""
        logger.warning(f"⚠️ USING SIMULATION MODE for {symbol} (API Keys failed)")
        return {
            "title": f"Cours complet sur le {symbol} (Mode Simulation)",
            "description": f"Ceci est un contenu généré automatiquement car aucune clé API valide n'a été trouvée. Ce cours couvre les bases du trading du {symbol}.",
            "content": {
                "sections": [
                    {
                        "id": "L1", 
                        "title": f"Introduction au {symbol}", 
                        "type": "TEXT", 
                        "data": f"Le {symbol} est un actif financier important. Dans cette section, nous allons explorer ses fondamentaux et pourquoi il est populaire auprès des traders.", 
                        "duration": 5
                    },
                    {
                        "id": "L2", 
                        "title": "Analyse Technique", 
                        "type": "TEXT", 
                        "data": "L'analyse technique consiste à étudier les graphiques pour prévoir les mouvements futurs. Regardez les tendances haussières et baissières.", 
                        "duration": 10
                    },
                    {
                        "id": "L3", 
                        "title": "Gestion des Risques", 
                        "type": "TEXT", 
                        "data": "Ne jamais investir plus que ce que vous pouvez vous permettre de perdre. Utilisez toujours des Stop-Loss.", 
                        "duration": 8
                    },
                    {
                        "id": "L4", 
                        "title": "Conclusion", 
                        "type": "TEXT", 
                        "data": "Vous avez maintenant les bases. Continuez à pratiquer sur un compte démo avant de passer au réel.", 
                        "duration": 5
                    },
                    {
                        "id": "L5", 
                        "title": "Ressources", 
                        "type": "TEXT", 
                        "data": "Consultez les actualités économiques et les calendriers financiers régulièrement.", 
                        "duration": 3
                    }
                ]
            },
            "quiz": {
                "questions": [
                    {
                        "question": "Quelle est la règle d'or du trading ?",
                        "options": ["Tout miser", "Gérer son risque", "Ignorer les graphiques", "Suivre la foule"],
                        "correctAnswer": 1
                    },
                    {
                        "question": f"Le {symbol} est-il volatil ?",
                        "options": ["Jamais", "Parfois", "Toujours", "Cela dépend du marché"],
                        "correctAnswer": 3
                    },
                    {
                        "question": "Que signifie Stop-Loss ?",
                        "options": ["Arrêter de perdre", "Gagner plus", "Ouvrir une position", "Fermer l'ordinateur"],
                        "correctAnswer": 0
                    },
                    {
                        "question": "L'analyse technique utilise :",
                        "options": ["Les étoiles", "Les graphiques", "Les rumeurs", "Le hasard"],
                        "correctAnswer": 1
                    },
                    {
                        "question": "Quand faut-il trader ?",
                        "options": ["Tout le temps", "Quand on s'ennuie", "Quand une opportunité se présente", "La nuit uniquement"],
                        "correctAnswer": 2
                    }
                ]
            }
        }

    async def generate_course_content(self, symbol: str, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate content, falling back to Mock Data if APIs fail"""
        
        # 1. Try Real AI Generation
        try:
            # Check if we have ANY valid client before trying
            if not self.client and not self.openai_client and not self.groq_key:
                logger.error("❌ No API keys configured.")
                return self._get_mock_course(symbol)

            market_str = json.dumps(market_data, indent=2) if market_data else "N/A"
            prompt = f"""
            Agis comme un expert trading. Crée un cours sur {symbol}.
            Données: {market_str}
            
            Format JSON EXCLUSIF (RFC8259):
            {{
              "title": "Titre", "description": "Desc",
              "content": {{ "sections": [ {{ "id": "1", "title": "T", "type": "TEXT", "data": "Content", "duration": 5 }} ] }},
              "quiz": {{ "questions": [ {{ "question": "Q", "options": ["A","B","C","D"], "correctAnswer": 0 }} ] }}
            }}
            Important: Minimum 5 sections, 5 questions.
            """

            response_text = ""

            # Try OpenAI
            if self.openai_client:
                try:
                    resp = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"}
                    )
                    response_text = resp.choices[0].message.content
                except Exception as e:
                    logger.warning(f"OpenAI failed: {e}")

            # Try Gemini
            if not response_text and self.client:
                try:
                    resp = self.client.generate_content(prompt)
                    response_text = resp.text
                except Exception as e:
                    logger.error(f"Gemini API failed: {e}")

            # Try Groq
            if not response_text and self.groq_key:
                try:
                    from groq import Groq
                    g_client = Groq(api_key=self.groq_key)
                    resp = g_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile",
                        response_format={"type": "json_object"}
                    )
                    response_text = resp.choices[0].message.content
                except Exception as e:
                    logger.error(f"Groq failed: {e}")

            # Parse Response
            if response_text:
                # Basic cleaning
                if "```" in response_text:
                    response_text = response_text.split("```json")[-1].split("```")[0] if "```json" in response_text else response_text.split("```")[1]
                
                try:
                    data = json.loads(response_text)
                    # Validate basic structure
                    if "content" in data and "sections" in data["content"]:
                        return data
                except Exception:
                    logger.error("Failed to parse JSON from AI")

            # If we get here, AI failed or JSON was bad
            return self._get_mock_course(symbol)

        except Exception as e:
            logger.error(f"Critical error in generation: {e}")
            return self._get_mock_course(symbol)

    async def generate_chat_response(self, prompt: str, context: str = "") -> str:
        """
        Generate a chat response using AI (OpenAI, Gemini, or Groq)
        
        Args:
            prompt: User's question
            context: Additional context (formation progress, etc.)
            
        Returns:
            AI response as a string
        """
        try:
            # Build the full prompt with context
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
            
            # Try OpenAI first (Primary)
            if self.openai_client:
                try:
                    resp = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a helpful trading education assistant. Answer questions clearly and concisely."},
                            {"role": "user", "content": full_prompt}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    return resp.choices[0].message.content
                except Exception as e:
                    logger.warning(f"OpenAI chat failed: {e}")
            
            # Try Gemini (Secondary)
            if self.client:
                try:
                    resp = self.client.generate_content(full_prompt)
                    return resp.text
                except Exception as e:
                    logger.warning(f"Gemini chat failed: {e}")
            
            # Try Groq (Fallback)
            if self.groq_key:
                try:
                    from groq import Groq
                    g_client = Groq(api_key=self.groq_key)
                    resp = g_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a helpful trading education assistant."},
                            {"role": "user", "content": full_prompt}
                        ],
                        model="llama-3.3-70b-versatile",
                        max_tokens=500
                    )
                    return resp.choices[0].message.content
                except Exception as e:
                    logger.warning(f"Groq chat failed: {e}")
            
            # Fallback response if all APIs fail
            logger.warning("All AI APIs failed, returning fallback response")
            return "I apologize, but I'm currently unable to process your request. Please ensure your API keys are configured correctly."
            
        except Exception as e:
            logger.error(f"Error in generate_chat_response: {e}")
            return f"I encountered an error: {str(e)}. Please try again later."

# Global instance
gemini_service = GeminiService()