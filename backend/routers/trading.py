from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import schemas
import services.trading_service as trading_service

router = APIRouter(
    prefix="/api/trading",
    tags=["Trading"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/history",
    response_model=schemas.TradingHistoryResponse,
    summary="Get OHLCV historical data for a symbol"
)
def get_trading_history(
    symbol: str = Query(..., description="The trading symbol, e.g., 'BTC-USD'"),
    timeframe: str = Query(..., description="The timeframe, e.g., '5m', '1h', '1d'"),
    db: Session = Depends(get_db)
):
    """
    Provides aggregated OHLCV (Open, High, Low, Close, Volume) data for a given
    trading symbol and timeframe.
    """
    try:
        ohlcv_data = trading_service.get_ohlcv_data(db=db, symbol=symbol, timeframe=timeframe)
        if not ohlcv_data:
            # Return a valid empty response if no data is found
            return schemas.TradingHistoryResponse(symbol=symbol, timeframe=timeframe, data=[])
            
        return schemas.TradingHistoryResponse(
            symbol=symbol,
            timeframe=timeframe,
            data=ohlcv_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for other potential errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

