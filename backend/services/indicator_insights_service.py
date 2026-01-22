"""
Indicator Insights Service
Computes technical indicators and simple sentiment from OHLCV data.
Optionally integrates with Groq to generate professional natural-language insights.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services import trading_service
from services.ai_assistant_service import ai_assistant_service
from services.news_service import news_service


@dataclass
class IndicatorSnapshot:
    symbol: str
    timeframe: str
    rsi14: Optional[float]
    macd: Optional[float]
    sma50: Optional[float]
    ema20: Optional[float]
    bb_basis: Optional[float]
    bb_upper: Optional[float]
    bb_lower: Optional[float]
    last_close: Optional[float]
    change_percent_24h: Optional[float]


class IndicatorInsightsService:
    """Compute indicators and derive simple sentiment for a trading symbol."""

    def get_snapshot(self, db: Session, symbol: str, timeframe: str) -> IndicatorSnapshot:
        ohlcv = trading_service.get_ohlcv_data(db=db, symbol=symbol, timeframe=timeframe)
        if not ohlcv or len(ohlcv) < 30:
            return IndicatorSnapshot(
                symbol=symbol,
                timeframe=timeframe,
                rsi14=None,
                macd=None,
                sma50=None,
                ema20=None,
                bb_basis=None,
                bb_upper=None,
                bb_lower=None,
                last_close=ohlcv[-1].close if ohlcv else None,
                change_percent_24h=None,
            )

        closes = [c.close for c in ohlcv]

        rsi14_series = self._calculate_rsi_series(closes, 14)
        ema_fast = self._calculate_ema_series(closes, 12)
        ema_slow = self._calculate_ema_series(closes, 26)
        macd_line = [
            (f - s) if f is not None and s is not None else None
            for f, s in zip(ema_fast, ema_slow)
        ]
        sma50_series = self._calculate_sma_series(closes, 50)
        ema20_series = self._calculate_ema_series(closes, 20)
        bb_basis, bb_upper, bb_lower = self._calculate_bollinger_series(closes, 20, 2.0)

        last_idx = len(closes) - 1
        last_close = closes[-1]

        # Rough 24h change using last ~24 candles (works best on 1h timeframe)
        lookback = min(24, len(closes) - 1)
        change_24h = None
        if lookback > 0:
            ref_price = closes[-(lookback + 1)]
            if ref_price:
                change_24h = (last_close - ref_price) / ref_price * 100.0

        return IndicatorSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            rsi14=rsi14_series[last_idx],
            macd=macd_line[last_idx],
            sma50=sma50_series[last_idx],
            ema20=ema20_series[last_idx],
            bb_basis=bb_basis[last_idx],
            bb_upper=bb_upper[last_idx],
            bb_lower=bb_lower[last_idx],
            last_close=last_close,
            change_percent_24h=change_24h,
        )

    # ----- Indicator series helpers -----

    def _calculate_rsi_series(self, closes: List[float], period: int) -> List[Optional[float]]:
        n = len(closes)
        if n < period + 1:
            return [None] * n

        gains: List[float] = []
        losses: List[float] = []
        for i in range(1, n):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0.0))
            losses.append(max(-diff, 0.0))

        # Seed averages
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        rsi: List[Optional[float]] = [None] * n
        # First RSI value corresponds to index period
        rs = 0.0 if avg_loss == 0 else avg_gain / avg_loss
        rsi_val = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + rs)
        rsi[period] = rsi_val

        # Wilder smoothing
        for i in range(period + 1, n):
            gain = gains[i - 1]
            loss = losses[i - 1]
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            rs = 0.0 if avg_loss == 0 else avg_gain / avg_loss
            rsi_val = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + rs)
            rsi[i] = rsi_val

        return rsi

    def _calculate_sma_series(self, closes: List[float], period: int) -> List[Optional[float]]:
        n = len(closes)
        result: List[Optional[float]] = [None] * n
        if n < period:
            return result

        window_sum = sum(closes[:period])
        result[period - 1] = window_sum / period
        for i in range(period, n):
            window_sum += closes[i] - closes[i - period]
            result[i] = window_sum / period
        return result

    def _calculate_ema_series(self, closes: List[float], period: int) -> List[Optional[float]]:
        n = len(closes)
        result: List[Optional[float]] = [None] * n
        if n < period:
            return result

        k = 2.0 / (period + 1)
        # start with SMA
        sma = sum(closes[:period]) / period
        ema = sma
        result[period - 1] = ema

        for i in range(period, n):
            ema = closes[i] * k + ema * (1.0 - k)
            result[i] = ema

        return result

    def _calculate_bollinger_series(
        self, closes: List[float], period: int, std_mult: float
    ) -> tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        n = len(closes)
        basis: List[Optional[float]] = [None] * n
        upper: List[Optional[float]] = [None] * n
        lower: List[Optional[float]] = [None] * n

        if n < period:
            return basis, upper, lower

        for i in range(period - 1, n):
            window = closes[i - period + 1 : i + 1]
            mean = sum(window) / period
            var = sum((v - mean) ** 2 for v in window) / period
            std = var ** 0.5

            basis[i] = mean
            upper[i] = mean + std_mult * std
            lower[i] = mean - std_mult * std

        return basis, upper, lower

    def build_rule_based_insight(self, snapshot: IndicatorSnapshot) -> Dict[str, Any]:
        """Fallback explanation without external AI."""
        if snapshot.last_close is None:
            return {
                "summary": "Not enough data to generate insights for this symbol/timeframe.",
                "sentiment_label": "neutral",
                "risk_level": "high",
                "bullets": [],
                "news": [],
                "indicators": snapshot.__dict__,
            }

        bullets: List[str] = []
        score = 0.0

        # RSI contribution
        if snapshot.rsi14 is not None:
            rsi = snapshot.rsi14
            if rsi > 70:
                bullets.append(f"RSI(14) is {rsi:.1f}, indicating overbought conditions.")
                score -= 0.5
            elif rsi < 30:
                bullets.append(f"RSI(14) is {rsi:.1f}, indicating oversold conditions.")
                score += 0.5
            elif rsi > 55:
                bullets.append(f"RSI(14) is {rsi:.1f}, showing moderate bullish momentum.")
                score += 0.2
            elif rsi < 45:
                bullets.append(f"RSI(14) is {rsi:.1f}, showing moderate bearish momentum.")
                score -= 0.2

        # MACD contribution
        if snapshot.macd is not None:
            if snapshot.macd > 0:
                bullets.append("MACD is above zero, confirming bullish momentum.")
                score += 0.3
            elif snapshot.macd < 0:
                bullets.append("MACD is below zero, confirming bearish momentum.")
                score -= 0.3

        # Trend vs moving averages
        if snapshot.ema20 is not None and snapshot.sma50 is not None and snapshot.last_close:
            if snapshot.last_close > snapshot.ema20 > snapshot.sma50:
                bullets.append(
                    "Price is trading above EMA(20) and SMA(50), indicating a short-term uptrend."
                )
                score += 0.3
            elif snapshot.last_close < snapshot.ema20 < snapshot.sma50:
                bullets.append(
                    "Price is below EMA(20) and SMA(50), indicating a short-term downtrend."
                )
                score -= 0.3

        # Bollinger Bands
        if (
            snapshot.bb_upper is not None
            and snapshot.bb_lower is not None
            and snapshot.last_close is not None
        ):
            if snapshot.last_close >= snapshot.bb_upper:
                bullets.append(
                    "Price is at or above the upper Bollinger Band, suggesting stretched upside and higher pullback risk."
                )
                score -= 0.4
            elif snapshot.last_close <= snapshot.bb_lower:
                bullets.append(
                    "Price is at or below the lower Bollinger Band, suggesting potential exhaustion on the downside."
                )
                score += 0.4

        # 24h change
        if snapshot.change_percent_24h is not None:
            cp = snapshot.change_percent_24h
            bullets.append(f"Approx. 24h change is {cp:+.2f}%.")
            if cp > 5:
                score += 0.2
            elif cp < -5:
                score -= 0.2

        # Derive sentiment label based on Fear & Greed Index (calculated below)
        # We'll set this after calculating the index for better accuracy
        sentiment = "neutral"  # Will be updated based on fear_greed_index

        # Calculate Fear & Greed Index (0-100 scale) with improved accuracy
        # Use weighted combination of multiple factors for better accuracy
        
        fg_score = 50.0  # Start at neutral (50)
        
        # RSI contribution (0-30 points)
        if snapshot.rsi14 is not None:
            rsi = snapshot.rsi14
            if rsi >= 70:  # Overbought = Greed
                fg_score += (rsi - 70) / 30 * 30  # Maps 70-100 RSI to +0 to +30
            elif rsi <= 30:  # Oversold = Fear
                fg_score -= (30 - rsi) / 30 * 30  # Maps 30-0 RSI to -0 to -30
        
        # MACD contribution (0-15 points)
        if snapshot.macd is not None:
            # Normalize MACD contribution (assume typical range -500 to +500)
            macd_norm = max(-1.0, min(1.0, snapshot.macd / 500.0))
            fg_score += macd_norm * 15
        
        # Price vs Moving Averages (0-15 points)
        if snapshot.ema20 is not None and snapshot.sma50 is not None and snapshot.last_close:
            if snapshot.last_close > snapshot.ema20 > snapshot.sma50:
                fg_score += 15  # Strong uptrend = Greed
            elif snapshot.last_close < snapshot.ema20 < snapshot.sma50:
                fg_score -= 15  # Strong downtrend = Fear
            elif snapshot.last_close > snapshot.ema20:
                fg_score += 7  # Above EMA = slight Greed
            elif snapshot.last_close < snapshot.ema20:
                fg_score -= 7  # Below EMA = slight Fear
        
        # 24h Change contribution (0-20 points)
        if snapshot.change_percent_24h is not None:
            change = snapshot.change_percent_24h
            # Normalize: +20% = +20 points, -20% = -20 points
            fg_score += max(-20, min(20, change))
        
        # Bollinger Bands position (0-10 points)
        if (
            snapshot.bb_upper is not None
            and snapshot.bb_lower is not None
            and snapshot.last_close is not None
        ):
            bb_range = snapshot.bb_upper - snapshot.bb_lower
            if bb_range > 0:
                # Position within bands: 0 = lower band (Fear), 1 = upper band (Greed)
                bb_position = (snapshot.last_close - snapshot.bb_lower) / bb_range
                fg_score += (bb_position - 0.5) * 20  # Maps 0-1 to -10 to +10
        
        # Clamp to 0-100 range
        fear_greed_index = int(max(0, min(100, fg_score)))
        
        # Derive sentiment label based on Fear & Greed Index
        if fear_greed_index >= 75:
            sentiment = "bullish"
        elif fear_greed_index >= 55:
            sentiment = "slightly_bullish"
        elif fear_greed_index >= 45:
            sentiment = "neutral"
        elif fear_greed_index >= 25:
            sentiment = "slightly_bearish"
        else:
            sentiment = "bearish"

        # Risk level: Calculate based on multiple volatility and extreme indicators
        risk_factors = []
        risk_score = 0.0
        
        # Factor 1: RSI extremes (overbought/oversold = higher risk)
        if snapshot.rsi14 is not None:
            rsi = snapshot.rsi14
            if rsi > 75 or rsi < 25:  # Extreme overbought/oversold
                risk_score += 1.5
                risk_factors.append("extreme_rsi")
            elif rsi > 70 or rsi < 30:  # Overbought/oversold
                risk_score += 1.0
                risk_factors.append("rsi_extreme")
        
        # Factor 2: Bollinger Band position (outside bands = higher volatility/risk)
        if (
            snapshot.bb_upper is not None
            and snapshot.bb_lower is not None
            and snapshot.last_close is not None
        ):
            bb_range = snapshot.bb_upper - snapshot.bb_lower
            if bb_range > 0:
                # Calculate how far outside the bands
                if snapshot.last_close >= snapshot.bb_upper:
                    distance = (snapshot.last_close - snapshot.bb_upper) / bb_range
                    risk_score += min(1.5, distance * 2)  # Up to 1.5 for extreme positions
                    risk_factors.append("above_bb")
                elif snapshot.last_close <= snapshot.bb_lower:
                    distance = (snapshot.bb_lower - snapshot.last_close) / bb_range
                    risk_score += min(1.5, distance * 2)
                    risk_factors.append("below_bb")
        
        # Factor 3: 24h change magnitude (large moves = higher risk)
        if snapshot.change_percent_24h is not None:
            abs_change = abs(snapshot.change_percent_24h)
            if abs_change > 15:  # Very large move
                risk_score += 1.5
                risk_factors.append("high_volatility")
            elif abs_change > 10:  # Large move
                risk_score += 1.0
                risk_factors.append("moderate_volatility")
            elif abs_change > 5:  # Moderate move
                risk_score += 0.5
        
        # Factor 4: MACD divergence (strong momentum = potential reversal risk)
        if snapshot.macd is not None:
            abs_macd = abs(snapshot.macd)
            # Very strong MACD can indicate overextension
            if abs_macd > 1000:  # Adjust threshold based on typical MACD values
                risk_score += 0.5
        
        # Determine risk level based on cumulative risk score
        if risk_score >= 2.5:
            risk = "high"
        elif risk_score >= 1.5:
            risk = "elevated"
        elif risk_score >= 0.8:
            risk = "medium"
        else:
            risk = "low"

        summary = (
            f"Based on current indicators, market tone for {snapshot.symbol} "
            f"on the {snapshot.timeframe} timeframe looks {sentiment} with {risk} risk."
        )

        # Fetch external news (if configured)
        # Fetch news with timeout protection - don't block if it fails
        try:
            news_items = news_service.get_symbol_news(snapshot.symbol)
        except Exception as e:
            print(f"[INDICATOR] News fetch failed (non-blocking): {e}")
            news_items = []  # Return empty list if news fails

        return {
            "summary": summary,
            "sentiment_label": sentiment,
            "fear_greed_index": fear_greed_index,  # Add proper 0-100 index
            "risk_level": risk,
            "bullets": bullets,
            "news": news_items,
            "indicators": snapshot.__dict__,
        }

    async def build_ai_insight(self, snapshot: IndicatorSnapshot) -> Dict[str, Any]:
        """
        If Groq is configured, ask it for a professional explanation.
        Falls back to rule-based insight if AI is not available.
        """
        if ai_assistant_service.client is None:
            result = self.build_rule_based_insight(snapshot)
            print(f"📰 build_rule_based_insight returned {len(result.get('news', []))} news items")
            return result

        indicators_payload = snapshot.__dict__
        user_message = (
            "You are a professional crypto technical analyst. "
            "Given the following JSON of indicator values for one symbol and timeframe, "
            "provide a concise expert insight.\n\n"
            f"INDICATORS_JSON:\n{indicators_payload}\n\n"
            "Respond strictly in JSON with the following keys:\n"
            "{"
            '"summary": string,'
            '"sentiment_label": "bullish" | "bearish" | "neutral",'
            '"risk_level": "low" | "medium" | "elevated" | "high",'
            '"bullets": string[],'
            '"news": []'
            "}\n"
            "Do not mention that you are an AI model. Be realistic and risk-aware, and never promise profits."
        )

        try:
            response_text = await ai_assistant_service.get_response(
                user_message=user_message,
                conversation_history=[],
                user_data=None,
            )
            # get_response returns plain text; if it's valid JSON we can eval it,
            # otherwise just wrap it.
            import json

            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, dict):
                    parsed.setdefault("indicators", indicators_payload)
                    # Ensure fear_greed_index is included (calculate from rule-based if not provided)
                    if "fear_greed_index" not in parsed:
                        rule_based = self.build_rule_based_insight(snapshot)
                        parsed["fear_greed_index"] = rule_based.get("fear_greed_index", 50)
                    # Ensure news is included from rule-based (AI might not return news)
                    if "news" not in parsed or not parsed.get("news"):
                        rule_based = self.build_rule_based_insight(snapshot)
                        parsed["news"] = rule_based.get("news", [])
                    print(f"📰 build_ai_insight (Groq) returning {len(parsed.get('news', []))} news items")
                    return parsed
            except Exception:
                pass

            # Fallback: wrap original text into rule-based structure
            base = self.build_rule_based_insight(snapshot)
            base["summary"] = response_text
            print(f"📰 build_ai_insight (fallback) returning {len(base.get('news', []))} news items")
            return base
        except Exception:
            result = self.build_rule_based_insight(snapshot)
            print(f"📰 build_ai_insight (exception) returning {len(result.get('news', []))} news items")
            return result


indicator_insights_service = IndicatorInsightsService()


