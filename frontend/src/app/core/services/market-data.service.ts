import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, interval } from 'rxjs';
import { tap, switchMap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface CryptoPrice {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number;
  timestamp: string;
  source: string;
}

export interface MarketDataResponse {
  prices: { [key: string]: CryptoPrice };
  active_source: string;
  last_update: string;
}

@Injectable({
  providedIn: 'root'
})
export class MarketDataService {
  private apiUrl = `${environment.apiUrl}/market`;
  private pricesSubject = new BehaviorSubject<MarketDataResponse | null>(null);
  public prices$ = this.pricesSubject.asObservable();

  constructor(private http: HttpClient) {
    // Start polling for price updates every 30 seconds
    this.startPricePolling();
  }

  private startPricePolling(): void {
    // Initial load
    this.getAllPrices().subscribe();

    // Poll every 30 seconds
    interval(30000)
      .pipe(switchMap(() => this.getAllPrices()))
      .subscribe();
  }

  getAllPrices(): Observable<MarketDataResponse> {
    return this.http.get<MarketDataResponse>(`${this.apiUrl}/prices`).pipe(
      tap(data => this.pricesSubject.next(data))
    );
  }

  getPrice(symbol: string): Observable<CryptoPrice> {
    return this.http.get<CryptoPrice>(`${this.apiUrl}/prices/${symbol}`);
  }

  getCurrentPrice(symbol: string): number | null {
    const currentData = this.pricesSubject.value;
    if (!currentData || !currentData.prices[symbol]) {
      return null;
    }
    return currentData.prices[symbol].price;
  }

  // Helper to get price for trading pairs like "BTC/USD"
  getPriceForPair(pair: string): number | null {
    const symbol = pair.replace('/', '-');
    return this.getCurrentPrice(symbol);
  }
}
