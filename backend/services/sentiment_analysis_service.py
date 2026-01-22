"""
Sentiment Analysis Service
Analyzes news sentiment and market mood for price predictions
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from services.news_service import news_service

logger = logging.getLogger(__name__)


class SentimentAnalysisService:
    """Service for analyzing market sentiment from news and social sources"""
    
    def __init__(self):
        self.sentiment_keywords = {
            "very_positive": ["moon", "rocket", "bullish", "surge", "explode", "skyrocket", "breakout", "rally", "boom"],
            "positive": ["up", "gain", "rise", "increase", "growth", "higher", "profit", "win", "success", "strong"],
            "negative": ["down", "fall", "drop", "crash", "decline", "loss", "weak", "fail", "sink", "plunge"],
            "very_negative": ["crash", "collapse", "disaster", "panic", "dump", "bloodbath", "massacre", "catastrophe"]
        }
    
    def analyze_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze news sentiment for a cryptocurrency
        
        Args:
            symbol: Cryptocurrency symbol (BTC, ETH, etc.)
            
        Returns:
            Dictionary with sentiment analysis results
        """
        try:
            # Get recent news
            news_items = news_service.get_symbol_news(f"{symbol}-USD", limit=20)
            
            if not news_items:
                return {
                    "sentiment_score": 0,
                    "sentiment": "neutral",
                    "confidence": 0,
                    "news_count": 0,
                    "reasoning": "No news available for analysis"
                }
            
            # Analyze each news item
            total_score = 0
            scored_items = 0
            sentiment_details = []
            
            for item in news_items:
                title = item.get("title", "").lower()
                summary = item.get("summary", "").lower()
                text = f"{title} {summary}"
                
                # Calculate sentiment score for this item
                score = self._calculate_text_sentiment(text)
                
                if score != 0:  # Only count items with sentiment
                    total_score += score
                    scored_items += 1
                    
                    sentiment_details.append({
                        "title": item.get("title", "")[:100],
                        "score": score,
                        "source": item.get("source", "unknown"),
                        "published": item.get("datetime", "")
                    })
            
            # Calculate overall sentiment
            if scored_items > 0:
                avg_score = total_score / scored_items
                confidence = min(100, (scored_items / 20) * 100)  # More news = higher confidence
            else:
                avg_score = 0
                confidence = 0
            
            # Determine sentiment category
            sentiment = self._score_to_sentiment(avg_score)
            
            return {
                "sentiment_score": round(avg_score, 2),  # Range: -100 to +100
                "sentiment": sentiment,
                "confidence": round(confidence, 0),
                "news_count": len(news_items),
                "scored_items": scored_items,
                "top_news": sentiment_details[:5],  # Top 5 news items
                "reasoning": self._generate_sentiment_reasoning(sentiment, avg_score, scored_items)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment for {symbol}: {e}")
            return {
                "sentiment_score": 0,
                "sentiment": "neutral",
                "confidence": 0,
                "news_count": 0,
                "reasoning": f"Error analyzing sentiment: {str(e)}"
            }
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """
        Calculate sentiment score for a piece of text
        
        Args:
            text: Text to analyze (lowercase)
            
        Returns:
            Sentiment score (-100 to +100)
        """
        score = 0
        
        # Check for very positive keywords
        for keyword in self.sentiment_keywords["very_positive"]:
            if keyword in text:
                score += 15
        
        # Check for positive keywords
        for keyword in self.sentiment_keywords["positive"]:
            if keyword in text:
                score += 5
        
        # Check for negative keywords
        for keyword in self.sentiment_keywords["negative"]:
            if keyword in text:
                score -= 5
        
        # Check for very negative keywords
        for keyword in self.sentiment_keywords["very_negative"]:
            if keyword in text:
                score -= 15
        
        # Normalize to -100 to +100 range
        return max(-100, min(100, score))
    
    def _score_to_sentiment(self, score: float) -> str:
        """Convert sentiment score to category"""
        if score >= 30:
            return "very_positive"
        elif score >= 10:
            return "positive"
        elif score <= -30:
            return "very_negative"
        elif score <= -10:
            return "negative"
        return "neutral"
    
    def _generate_sentiment_reasoning(self, sentiment: str, score: float, news_count: int) -> str:
        """Generate human-readable reasoning for sentiment"""
        sentiment_labels = {
            "very_positive": "Very Positive",
            "positive": "Positive",
            "neutral": "Neutral",
            "negative": "Negative",
            "very_negative": "Very Negative"
        }
        
        label = sentiment_labels.get(sentiment, "Neutral")
        
        return f"{label} market sentiment based on analysis of {news_count} recent news articles (score: {score:+.1f}/100)"
    
    def get_market_mood(self, symbols: List[str] = ["BTC", "ETH"]) -> Dict[str, Any]:
        """
        Get overall market mood across multiple cryptocurrencies
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            Aggregated market mood analysis
        """
        try:
            sentiments = {}
            total_score = 0
            total_confidence = 0
            
            for symbol in symbols:
                sentiment = self.analyze_news_sentiment(symbol)
                sentiments[symbol] = sentiment
                total_score += sentiment["sentiment_score"] * (sentiment["confidence"] / 100)
                total_confidence += sentiment["confidence"]
            
            # Calculate weighted average
            if total_confidence > 0:
                market_score = total_score / (len(symbols))
            else:
                market_score = 0
            
            market_mood = self._score_to_sentiment(market_score)
            
            return {
                "market_mood": market_mood,
                "market_score": round(market_score, 2),
                "individual_sentiments": sentiments,
                "summary": self._generate_market_summary(market_mood, market_score)
            }
            
        except Exception as e:
            logger.error(f"Error getting market mood: {e}")
            return {
                "market_mood": "neutral",
                "market_score": 0,
                "error": str(e)
            }
    
    def _generate_market_summary(self, mood: str, score: float) -> str:
        """Generate market summary text"""
        mood_descriptions = {
            "very_positive": "The overall market sentiment is extremely bullish with strong positive news flow.",
            "positive": "The market sentiment is optimistic with mostly positive news coverage.",
            "neutral": "The market sentiment is balanced with mixed news signals.",
            "negative": "The market sentiment is cautious with mostly negative news coverage.",
            "very_negative": "The overall market sentiment is bearish with strong negative news flow."
        }
        
        return mood_descriptions.get(mood, "Market sentiment is unclear.")


# Global instance
sentiment_service = SentimentAnalysisService()
