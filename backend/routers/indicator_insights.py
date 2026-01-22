"""
Indicator Insights Router
Provides AI-assisted technical indicator summary, sentiment, and (optionally) news.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from services.indicator_insights_service import indicator_insights_service


class NewsItem(BaseModel):
  title: str
  url: Optional[str] = None
  source: Optional[str] = None
  published_at: Optional[str] = None
  impact: Optional[str] = None  # low, medium, high


class IndicatorInsightResponse(BaseModel):
  symbol: str
  timeframe: str
  summary: str
  sentiment_label: str
  fear_greed_index: int  # 0-100 scale (0=Extreme Fear, 100=Extreme Greed)
  risk_level: str
  bullets: List[str]
  news: List[NewsItem]
  indicators: Dict[str, Any]


router = APIRouter(prefix="/api/ai", tags=["AI Indicator Insights"])


@router.get("/indicator-insights", response_model=IndicatorInsightResponse)
async def get_indicator_insights(
  symbol: str = Query(..., description="Trading symbol, e.g. BTC-USD"),
  timeframe: str = Query("1h", description="Timeframe, e.g. 1m, 5m, 1h, 1d"),
  db: Session = Depends(get_db),
):
  """
  Get an AI-powered but risk-aware interpretation of key indicators
  plus a simple sentiment/risk assessment for the given symbol/timeframe.
  """
  try:
    snapshot = indicator_insights_service.get_snapshot(db=db, symbol=symbol, timeframe=timeframe)

    if snapshot.last_close is None:
      raise HTTPException(
        status_code=400,
        detail="Not enough OHLCV data to compute indicator insights for this symbol/timeframe.",
      )

    ai_result = await indicator_insights_service.build_ai_insight(snapshot)

    # Normalize news into NewsItem list (service currently returns [] by default)
    raw_news = ai_result.get("news") or []
    print(f"📰 Router received {len(raw_news)} raw news items from service")
    news_items: List[NewsItem] = []
    for item in raw_news:
      if isinstance(item, dict):
        news_item = NewsItem(
          title=item.get("title", ""),
          url=item.get("url"),
          source=item.get("source"),
          published_at=item.get("published_at"),
          impact=item.get("impact"),
        )
        news_items.append(news_item)
        print(f"   ✓ Processed news item: {news_item.title[:50]}...")
      else:
        print(f"   ⚠️ Skipped invalid news item (not a dict): {type(item)}")
    
    print(f"📰 Router returning {len(news_items)} news items to frontend")

    return IndicatorInsightResponse(
      symbol=snapshot.symbol,
      timeframe=snapshot.timeframe,
      summary=ai_result.get("summary", ""),
      sentiment_label=ai_result.get("sentiment_label", "neutral"),
      fear_greed_index=ai_result.get("fear_greed_index", 50),  # Default to neutral (50)
      risk_level=ai_result.get("risk_level", "medium"),
      bullets=ai_result.get("bullets", []),
      news=news_items,
      indicators=ai_result.get("indicators", snapshot.__dict__),
    )
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed to generate indicator insights: {e}")


