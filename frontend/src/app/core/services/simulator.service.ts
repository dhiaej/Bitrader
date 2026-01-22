import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SimulatorResultCreate {
  pair: string;
  start_date: string;  // ISO date string
  end_date: string;    // ISO date string
  entry_price: number;
  stop_loss: number;
  take_profit: number;
}

export interface SimulatorCalculation {
  exit_price: number;
  pnl_percent: number;
  is_win: boolean;
  hit_type: string;  // "TP", "SL", or "END"
  message: string;
}

export interface SimulatorResult {
  id: number;
  user_id: number;
  username: string;
  pair: string;
  start_date: string;
  end_date: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  exit_price: number;
  pnl_percent: number;
  is_win: boolean;
  hit_type: string;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  username: string;
  pair: string;
  pnl_percent: number;
  is_win: boolean;
  created_at: string;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total_count: number;
}

export interface OHLCVData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface TradingHistoryResponse {
  symbol: string;
  timeframe: string;
  data: OHLCVData[];
}

export interface PriceAtDateResponse {
  symbol: string;
  date: string;
  price: number;
}

@Injectable({
  providedIn: 'root'
})
export class SimulatorService {
  private apiUrl = 'http://localhost:8000/api/simulator';

  constructor(private http: HttpClient) {}

  /**
   * Get historical OHLCV data for a specific date range
   */
  getHistoricalData(
    symbol: string,
    startDate: Date,
    endDate: Date,
    interval: string = '1h'
  ): Observable<TradingHistoryResponse> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('start_date', startDate.toISOString())
      .set('end_date', endDate.toISOString())
      .set('interval', interval);

    return this.http.get<TradingHistoryResponse>(`${this.apiUrl}/historical-data`, { params });
  }

  /**
   * Calculate simulation result without saving
   */
  calculateResult(request: SimulatorResultCreate): Observable<SimulatorCalculation> {
    return this.http.post<SimulatorCalculation>(`${this.apiUrl}/calculate`, request);
  }

  /**
   * Save simulation result to database
   */
  saveResult(request: SimulatorResultCreate): Observable<SimulatorResult> {
    return this.http.post<SimulatorResult>(`${this.apiUrl}/save-result`, request);
  }

  /**
   * Get leaderboard sorted by PnL %
   */
  getLeaderboard(limit: number = 50, pair?: string): Observable<LeaderboardResponse> {
    let params = new HttpParams().set('limit', limit.toString());
    if (pair) {
      params = params.set('pair', pair);
    }
    return this.http.get<LeaderboardResponse>(`${this.apiUrl}/leaderboard`, { params });
  }

  /**
   * Get current user's simulation history
   */
  getMyResults(limit: number = 20): Observable<SimulatorResult[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<SimulatorResult[]>(`${this.apiUrl}/my-results`, { params });
  }

  /**
   * Get the price at a specific date
   */
  getPriceAtDate(symbol: string, date: Date): Observable<PriceAtDateResponse> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('date', date.toISOString());
    return this.http.get<PriceAtDateResponse>(`${this.apiUrl}/price-at-date`, { params });
  }
}

