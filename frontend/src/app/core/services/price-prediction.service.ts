/**
 * Price Prediction Service
 * Handles AI-powered price predictions for cryptocurrencies
 */
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, interval } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface PricePrediction {
  symbol: string;
  timeframe: string;
  prediction: 'up' | 'down' | 'neutral';
  predicted_change: number;
  confidence: number;
  current_price: number;
  predicted_price: number;
  recommendation: 'BUY' | 'SELL' | 'HOLD';
  reasoning: string;
  created_at?: string;

  // Enhanced prediction data
  key_factors?: string[];
  risk_assessment?: string;
  technical_analysis?: {
    rsi: number;
    rsi_signal: string;
    macd_crossover: string;
    trend_direction: string;
    bb_position: string;
    overall_signal_score: number;
  };
  sentiment_analysis?: {
    score: number;
    sentiment: string;
    confidence: number;
    news_count: number;
  };
  data_points_used?: number;
  volatility?: number;
  data_source?: string;
}

export interface AllPredictions {
  BTC: {
    '1h'?: PricePrediction;
    '24h'?: PricePrediction;
    '7d'?: PricePrediction;
  };
  ETH: {
    '1h'?: PricePrediction;
    '24h'?: PricePrediction;
    '7d'?: PricePrediction;
  };
  LTC?: {
    '1h'?: PricePrediction;
    '24h'?: PricePrediction;
    '7d'?: PricePrediction;
  };
  SOL?: {
    '1h'?: PricePrediction;
    '24h'?: PricePrediction;
    '7d'?: PricePrediction;
  };
  DOGE?: {
    '1h'?: PricePrediction;
    '24h'?: PricePrediction;
    '7d'?: PricePrediction;
  };
}

@Injectable({
  providedIn: 'root'
})
export class PricePredictionService {
  private apiUrl = `${environment.apiUrl}/predictions`;
  private predictionsSubject = new BehaviorSubject<AllPredictions | null>(null);

  predictions$ = this.predictionsSubject.asObservable();

  constructor(private http: HttpClient) {
    // Auto-refresh predictions every 30 minutes
    interval(30 * 60 * 1000).subscribe(() => {
      this.loadPredictions();
    });
  }

  /**
   * Load all predictions for all cryptocurrencies and timeframes
   * @param forceRefresh - Force fresh predictions, ignoring cache
   */
  loadPredictions(forceRefresh: boolean = false): Observable<any> {
    const options = forceRefresh ? { params: { force_refresh: 'true' } } : {};
    return this.http.get<any>(`${this.apiUrl}/all`, options).pipe(
      tap(response => {
        if (response.success) {
          this.predictionsSubject.next(response.predictions);
          console.log('Predictions updated:', response.predictions);
        }
      }),
      catchError(error => {
        console.error('Error loading predictions:', error);
        throw error;
      })
    );
  }

  /**
   * Get prediction for specific symbol and timeframe
   */
  getPrediction(symbol: string, timeframe: '1h' | '24h' | '7d'): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${symbol}/${timeframe}`);
  }

  /**
   * Get prediction badge configuration for UI display
   */
  getPredictionBadge(prediction: PricePrediction | undefined): {
    text: string;
    class: string;
    icon: string;
    show: boolean;
  } {
    if (!prediction) {
      return { text: '', class: '', icon: '', show: false };
    }

    const direction = prediction.prediction;
    const change = prediction.predicted_change;
    const confidence = prediction.confidence;

    // Only show badge if confidence is above 40%
    if (confidence < 40) {
      return { text: '', class: '', icon: '', show: false };
    }

    let text = '';
    let cssClass = '';
    let icon = '';

    if (direction === 'up') {
      text = `AI: +${change.toFixed(1)}% ${prediction.timeframe}`;
      cssClass = 'prediction-badge-up';
      icon = '📈';
    } else if (direction === 'down') {
      text = `AI: ${change.toFixed(1)}% ${prediction.timeframe}`;
      cssClass = 'prediction-badge-down';
      icon = '📉';
    } else {
      text = `AI: Neutral ${prediction.timeframe}`;
      cssClass = 'prediction-badge-neutral';
      icon = '➡️';
    }

    return {
      text: `${icon} ${text} (${confidence}% confident)`,
      class: cssClass,
      icon,
      show: true
    };
  }

  /**
   * Get recommendation color and icon
   */
  getRecommendationStyle(recommendation: string): {
    color: string;
    icon: string;
    text: string;
  } {
    switch (recommendation) {
      case 'BUY':
        return { color: 'success', icon: '🚀', text: 'Strong Buy' };
      case 'SELL':
        return { color: 'danger', icon: '⚠️', text: 'Consider Selling' };
      case 'HOLD':
      default:
        return { color: 'warning', icon: '⏸️', text: 'Hold Position' };
    }
  }
}
