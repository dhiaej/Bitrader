"""
AI Trading Assistant Service
Provides intelligent trading advice and platform help using Groq (FREE & FAST)
"""
from typing import Dict, Any, List, Optional
import logging

from config import settings
from services.market_data_service import market_data_service

logger = logging.getLogger(__name__)

try:
    # Optional dependency – backend should still run if Groq SDK is not installed
    from groq import Groq  # type: ignore
except ImportError:
    Groq = None  # type: ignore
    logger.warning(
        "groq package is not installed. AI assistant endpoints will return a "
        "configuration error until you install 'groq' and set GROQ_API_KEY."
    )


class AIAssistantService:
    """Service for AI-powered trading assistance"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = None
        if settings.GROQ_API_KEY and Groq is not None:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning(
                "Groq client not initialized - either GROQ_API_KEY is missing "
                "or the 'groq' package is not installed. "
                "AI Assistant endpoints will return a configuration message."
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines the AI assistant's behavior"""
        return """You are an expert AI Trading Assistant for a P2P cryptocurrency trading platform. Your role is to:

1. Help users understand cryptocurrency trading, P2P trading, and the platform features
2. Provide market insights based on real-time crypto prices
3. Give personalized trading advice based on user's wallet balances
4. Explain trading concepts in simple, beginner-friendly language
5. Always prioritize user safety and responsible trading

Important guidelines:
- Be friendly, helpful, and professional
- Use the user's actual wallet data and current market prices when giving advice
- Never guarantee profits or promise returns
- Encourage responsible trading and risk management
- Explain P2P trading: users create ads, platform auto-matches opposite ads, uses escrow for safety
- For price questions, always reference the current live prices provided
- Keep responses concise but informative (2-4 sentences usually)
- Use emojis occasionally to be engaging 📊💰📈

Platform Features:
- Auto-matching P2P system: When you create a BUY/SELL ad, the system automatically finds matching SELL/BUY ads
- Escrow protection: Funds are locked safely until both parties confirm
- Real-time prices from CoinGecko/Binance
- Order book for limit/market orders
- Wallet system for BTC, ETH, USD, USDT
"""
    
    def _build_context(self, user_data: Optional[Dict[str, Any]] = None) -> str:
        """Build context string with current market data and user info"""
        context_parts = []
        
        # Add current market prices
        market_data = market_data_service.get_all_prices()
        if market_data and market_data.get("prices"):
            context_parts.append("CURRENT MARKET PRICES:")
            for symbol, price_data in market_data["prices"].items():
                if price_data:
                    change_emoji = "📈" if price_data.get("change_percent", 0) >= 0 else "📉"
                    context_parts.append(
                        f"{symbol}: ${price_data.get('price', 0):,.2f} "
                        f"{change_emoji} {price_data.get('change_percent', 0):+.2f}% (24h)"
                    )
        
        # Add user's wallet data if provided
        if user_data:
            context_parts.append("\nUSER'S WALLET:")
            wallets = user_data.get("wallets", [])
            for wallet in wallets:
                context_parts.append(
                    f"{wallet['currency']}: "
                    f"Available: {float(wallet['available_balance']):.8f}, "
                    f"Locked: {float(wallet['locked_balance']):.8f}"
                )
            
            # Add trading history if available
            trades = user_data.get("recent_trades", [])
            if trades:
                context_parts.append(f"\nRECENT TRADES: {len(trades)} completed trades")
        
        return "\n".join(context_parts)
    
    async def get_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]], 
        user_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get AI response to user message
        
        Args:
            user_message: The user's question/message
            conversation_history: Previous messages in the conversation
            user_data: User's wallet balances and trading info
            
        Returns:
            AI assistant's response
        """
        if not self.client:
            return "❌ AI Assistant is not configured. Please add GROQ_API_KEY to environment variables."
        
        try:
            # Build context with current market data and user info
            context = self._build_context(user_data)
            
            # Prepare messages for Groq
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "system", "content": f"CURRENT CONTEXT:\n{context}"}
            ]
            
            # Add conversation history (last 10 messages to keep context manageable)
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Call Groq API (MUCH FASTER than OpenAI!)
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Latest Groq model (Nov 2024)
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            
            # Extract and return the response
            ai_response = response.choices[0].message.content
            logger.info(f"AI response generated for message: {user_message[:50]}...")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return f"❌ Sorry, I encountered an error: {str(e)}. Please try again."
    
    async def get_quick_suggestion(self, suggestion_type: str, user_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Get quick AI suggestions for common actions
        
        Args:
            suggestion_type: Type of suggestion ("market_analysis", "trading_tip", "risk_assessment")
            user_data: User's wallet and trading data
            
        Returns:
            Quick suggestion text
        """
        prompts = {
            "market_analysis": "Give a brief analysis of the current crypto market in 2-3 sentences.",
            "trading_tip": "Give one practical trading tip for a beginner crypto trader.",
            "risk_assessment": "Based on my current portfolio, what's my risk level and what should I be aware of?"
        }
        
        prompt = prompts.get(suggestion_type, "Give general trading advice.")
        return await self.get_response(prompt, [], user_data)


# Global instance
ai_assistant_service = AIAssistantService()
