"""
Simulator Router - Endpoints for the Trading Simulator / Backtesting Game
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import requests

from database import get_db
from models import User
from models.simulator_result import SimulatorResult
from utils.auth import get_current_user
import schemas

router = APIRouter(
    prefix="/api/simulator",
    tags=["Trading Simulator"],
    responses={404: {"description": "Not found"}},
)

BINANCE_API_URL = "https://api.binance.com/api/v3/klines"


def _map_symbol_to_binance(symbol: str) -> str:
    """Maps 'BTC-USD' → 'BTCUSDT', 'ETH-USD' → 'ETHUSDT', etc."""
    parts = symbol.upper().split("-")
    if len(parts) != 2:
        return f"{parts[0]}USDT"
    
    base, quote = parts
    if quote == "USD":
        quote = "USDT"
    return f"{base}{quote}"


def get_historical_klines(symbol: str, start_time: int, end_time: int, interval: str = "1h") -> list:
    """
    Fetch historical klines from Binance for a specific time range.
    
    Args:
        symbol: Trading pair (e.g., "BTC-USD")
        start_time: Start timestamp in milliseconds
        end_time: End timestamp in milliseconds
        interval: Kline interval (default "1h")
    
    Returns:
        List of klines data
    """
    binance_symbol = _map_symbol_to_binance(symbol)
    
    params = {
        "symbol": binance_symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000,  # Maximum allowed by Binance
    }
    
    try:
        res = requests.get(BINANCE_API_URL, params=params, timeout=15)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data from Binance: {e}")
        return []


def calculate_simulation_result(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    klines: list
) -> dict:
    """
    Calculate simulation result based on historical price data.
    
    Checks each candle to see if price hit TP or SL first.
    
    Returns:
        dict with exit_price, pnl_percent, is_win, hit_type, message
    """
    if not klines:
        return {
            "exit_price": entry_price,
            "pnl_percent": 0.0,
            "is_win": False,
            "hit_type": "END",
            "message": "No historical data available for this period."
        }
    
    # Determine if it's a long position (entry < TP) or handle both scenarios
    is_long = take_profit > entry_price
    
    for kline in klines:
        # Binance kline format: [open_time, open, high, low, close, volume, ...]
        high = float(kline[2])
        low = float(kline[3])
        close = float(kline[4])
        
        if is_long:
            # Long position: price going up is good
            # Check if SL was hit (price went below stop_loss)
            if low <= stop_loss:
                pnl = ((stop_loss - entry_price) / entry_price) * 100
                return {
                    "exit_price": stop_loss,
                    "pnl_percent": round(pnl, 2),
                    "is_win": False,
                    "hit_type": "SL",
                    "message": f"Stop Loss hit! Price dropped to {stop_loss:.2f}"
                }
            
            # Check if TP was hit (price went above take_profit)
            if high >= take_profit:
                pnl = ((take_profit - entry_price) / entry_price) * 100
                return {
                    "exit_price": take_profit,
                    "pnl_percent": round(pnl, 2),
                    "is_win": True,
                    "hit_type": "TP",
                    "message": f"Take Profit hit! Price reached {take_profit:.2f}"
                }
        else:
            # Short position: price going down is good
            # Check if SL was hit (price went above stop_loss)
            if high >= stop_loss:
                pnl = ((entry_price - stop_loss) / entry_price) * 100
                return {
                    "exit_price": stop_loss,
                    "pnl_percent": round(pnl, 2),
                    "is_win": False,
                    "hit_type": "SL",
                    "message": f"Stop Loss hit! Price rose to {stop_loss:.2f}"
                }
            
            # Check if TP was hit (price went below take_profit)
            if low <= take_profit:
                pnl = ((entry_price - take_profit) / entry_price) * 100
                return {
                    "exit_price": take_profit,
                    "pnl_percent": round(pnl, 2),
                    "is_win": True,
                    "hit_type": "TP",
                    "message": f"Take Profit hit! Price dropped to {take_profit:.2f}"
                }
    
    # Neither TP nor SL hit - use the last close price
    last_close = float(klines[-1][4])
    if is_long:
        pnl = ((last_close - entry_price) / entry_price) * 100
    else:
        pnl = ((entry_price - last_close) / entry_price) * 100
    
    return {
        "exit_price": last_close,
        "pnl_percent": round(pnl, 2),
        "is_win": pnl > 0,
        "hit_type": "END",
        "message": f"Period ended. Final price: {last_close:.2f}"
    }


@router.get(
    "/historical-data",
    response_model=schemas.TradingHistoryResponse,
    summary="Get historical OHLCV data for a specific date range"
)
def get_historical_data(
    symbol: str = Query(..., description="Trading pair, e.g., 'BTC-USD'"),
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    interval: str = Query("1h", description="Kline interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d"),
):
    """
    Fetches historical OHLCV data for the simulator chart.
    Used to display the masked chart data.
    """
    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    
    klines = get_historical_klines(symbol, start_ms, end_ms, interval)
    
    if not klines:
        return schemas.TradingHistoryResponse(symbol=symbol, timeframe=interval, data=[])
    
    ohlcv_data = []
    for kline in klines:
        ohlcv_data.append(schemas.OHLCVData(
            time=int(kline[0] // 1000),  # Convert ms to seconds
            open=float(kline[1]),
            high=float(kline[2]),
            low=float(kline[3]),
            close=float(kline[4]),
            volume=float(kline[5])
        ))
    
    return schemas.TradingHistoryResponse(
        symbol=symbol,
        timeframe=interval,
        data=ohlcv_data
    )


@router.post(
    "/calculate",
    response_model=schemas.SimulatorCalculation,
    summary="Calculate simulation result without saving"
)
def calculate_result(
    request: schemas.SimulatorResultCreate,
):
    """
    Calculates the simulation outcome based on the position parameters.
    This is called when the user clicks "Show Results".
    """
    start_ms = int(request.start_date.timestamp() * 1000)
    end_ms = int(request.end_date.timestamp() * 1000)
    
    # Fetch historical data for the simulation period
    klines = get_historical_klines(request.pair, start_ms, end_ms, "1h")
    
    # Calculate the result
    result = calculate_simulation_result(
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
        klines=klines
    )
    
    return schemas.SimulatorCalculation(**result)


@router.post(
    "/save-result",
    response_model=schemas.SimulatorResultResponse,
    summary="Save simulation result to database"
)
def save_result(
    request: schemas.SimulatorResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Saves the simulation result to the database for the leaderboard.
    """
    start_ms = int(request.start_date.timestamp() * 1000)
    end_ms = int(request.end_date.timestamp() * 1000)
    
    # Fetch historical data and calculate result
    klines = get_historical_klines(request.pair, start_ms, end_ms, "1h")
    result = calculate_simulation_result(
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
        klines=klines
    )
    
    # Create and save the result
    simulator_result = SimulatorResult(
        user_id=current_user.id,
        username=current_user.username,
        pair=request.pair,
        start_date=request.start_date,
        end_date=request.end_date,
        entry_price=request.entry_price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit,
        exit_price=result["exit_price"],
        pnl_percent=result["pnl_percent"],
        is_win=result["is_win"],
        hit_type=result["hit_type"]
    )
    
    db.add(simulator_result)
    db.commit()
    db.refresh(simulator_result)
    
    return simulator_result


@router.get(
    "/leaderboard",
    response_model=schemas.LeaderboardResponse,
    summary="Get the leaderboard sorted by PnL %"
)
def get_leaderboard(
    limit: int = Query(50, ge=1, le=100, description="Number of entries to return"),
    pair: Optional[str] = Query(None, description="Filter by trading pair"),
    db: Session = Depends(get_db),
):
    """
    Returns the leaderboard sorted by PnL % (highest first).
    Optionally filter by trading pair.
    """
    query = db.query(SimulatorResult)
    
    if pair:
        query = query.filter(SimulatorResult.pair == pair)
    
    # Get total count
    total_count = query.count()
    
    # Get sorted results
    results = query.order_by(desc(SimulatorResult.pnl_percent)).limit(limit).all()
    
    entries = []
    for rank, result in enumerate(results, 1):
        entries.append(schemas.LeaderboardEntry(
            rank=rank,
            username=result.username,
            pair=result.pair,
            pnl_percent=result.pnl_percent,
            is_win=result.is_win,
            created_at=result.created_at
        ))
    
    return schemas.LeaderboardResponse(entries=entries, total_count=total_count)


@router.get(
    "/my-results",
    response_model=List[schemas.SimulatorResultResponse],
    summary="Get current user's simulation results"
)
def get_my_results(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current user's simulation history.
    """
    results = (
        db.query(SimulatorResult)
        .filter(SimulatorResult.user_id == current_user.id)
        .order_by(desc(SimulatorResult.created_at))
        .limit(limit)
        .all()
    )
    
    return results


@router.get(
    "/price-at-date",
    summary="Get the price at a specific date for default entry price"
)
def get_price_at_date(
    symbol: str = Query(..., description="Trading pair, e.g., 'BTC-USD'"),
    date: datetime = Query(..., description="Date to get price for (ISO format)"),
):
    """
    Returns the opening price at the specified date.
    Used to set the default entry price in the simulator form.
    """
    # Get a small window around the date
    start_ms = int(date.timestamp() * 1000)
    end_ms = start_ms + (24 * 60 * 60 * 1000)  # Add 24 hours
    
    klines = get_historical_klines(symbol, start_ms, end_ms, "1h")
    
    if not klines:
        raise HTTPException(status_code=404, detail="No price data available for this date")
    
    # Return the opening price of the first candle
    return {
        "symbol": symbol,
        "date": date.isoformat(),
        "price": float(klines[0][1])  # Open price
    }

