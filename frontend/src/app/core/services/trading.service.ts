import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, timeout, catchError, throwError } from 'rxjs';
import { map } from 'rxjs/operators';

// Data format for a single candlestick
export interface OhlcvData {
  time: number; // Unix timestamp
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface IndicatorNewsItem {
  title: string;
  url?: string;
  source?: string;
  published_at?: string;
  impact?: string;
}

export interface IndicatorInsightResponse {
  symbol: string;
  timeframe: string;
  summary: string;
  sentiment_label: string;
  fear_greed_index: number; // 0-100 scale (0=Extreme Fear, 100=Extreme Greed)
  risk_level: string;
  bullets: string[];
  news: IndicatorNewsItem[];
  indicators: Record<string, any>;
}

// The expected response from the /api/trading/history endpoint
export interface TradingHistoryResponse {
  symbol: string;
  timeframe: string;
  data: OhlcvData[];
}

@Injectable({
  providedIn: 'root'
})
export class TradingService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  /**
   * Fetches OHLCV data from the backend.
   * @param symbol The trading symbol (e.g., 'BTC-USD').
   * @param timeframe The chart timeframe (e.g., '5m', '1h').
   * @returns An observable of the trading history response.
   */
  getOhlcvData(symbol: string, timeframe: string): Observable<TradingHistoryResponse> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('timeframe', timeframe);

    return this.http.get<TradingHistoryResponse>(`${this.apiUrl}/trading/history`, { params });
  }

  /**
   * Fetch AI-powered indicator insights (summary, sentiment, risk, news).
   */
  getIndicatorInsights(
    symbol: string,
    timeframe: string
  ): Observable<IndicatorInsightResponse> {
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('timeframe', timeframe);

    return this.http.get<IndicatorInsightResponse>(`${this.apiUrl}/ai/indicator-insights`, {
      params,
    }).pipe(
      timeout(30000), // 30 second timeout
      catchError((error) => {
        console.error('TradingService: Error fetching indicator insights', error);
        return throwError(() => error);
      })
    );
  }
}
