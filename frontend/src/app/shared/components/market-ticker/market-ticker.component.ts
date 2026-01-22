import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MarketDataService, MarketDataResponse, CryptoPrice } from '../../../core/services/market-data.service';
import { Subscription } from 'rxjs';

/**
 * Market Ticker Bar Component
 * Displays live cryptocurrency prices like Binance header
 * Shows BTC, ETH, LTC, SOL, DOGE with 24h change and volume
 */
@Component({
  selector: 'app-market-ticker',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="market-ticker-bar">
      <div class="ticker-container">
        <div
          *ngFor="let ticker of tickers"
          class="ticker-item"
          [class.positive]="ticker.change_percent > 0"
          [class.negative]="ticker.change_percent < 0"
          (click)="navigateToTrade(ticker.symbol)"
        >
          <div class="ticker-symbol">
            {{ ticker.symbol.replace('-USD', '') }}/USD
          </div>
          <div class="ticker-price">
            {{ formatPrice(ticker.price) }}
          </div>
          <div class="ticker-change" [class.positive]="ticker.change_percent > 0" [class.negative]="ticker.change_percent < 0">
            {{ ticker.change_percent > 0 ? '+' : '' }}{{ ticker.change_percent.toFixed(2) }}%
          </div>
          <div class="ticker-volume" *ngIf="ticker.volume">
            Vol: {{ formatVolume(ticker.volume) }}
          </div>
        </div>
      </div>

      <div class="ticker-status" *ngIf="lastUpdate">
        <span class="status-indicator" [class.active]="isLive"></span>
        <span class="status-text">{{ isLive ? 'LIVE' : 'UPDATING' }}</span>
        <span class="update-time">{{ getTimeAgo(lastUpdate) }}</span>
      </div>
    </div>
  `,
  styles: [`
    .market-ticker-bar {
      background: #1E2026;
      border-bottom: 1px solid #2B2F36;
      padding: 8px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      overflow-x: auto;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .ticker-container {
      display: flex;
      gap: 24px;
      align-items: center;
      flex: 1;
    }

    .ticker-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .ticker-item:hover {
      background: #2B2F36;
    }

    .ticker-symbol {
      font-size: 12px;
      font-weight: 600;
      color: #B7BDC6;
      min-width: 75px;
    }

    .ticker-price {
      font-size: 13px;
      font-weight: 600;
      color: #FFFFFF;
      min-width: 80px;
    }

    .ticker-change {
      font-size: 12px;
      font-weight: 500;
      padding: 2px 8px;
      border-radius: 4px;
      min-width: 60px;
      text-align: center;
    }

    .ticker-change.positive {
      color: #0ECB81;
      background: rgba(14, 203, 129, 0.1);
    }

    .ticker-change.negative {
      color: #F6465D;
      background: rgba(246, 70, 93, 0.1);
    }

    .ticker-volume {
      font-size: 11px;
      color: #5E6673;
      min-width: 80px;
    }

    .ticker-status {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      background: #2B2F36;
      border-radius: 6px;
      font-size: 11px;
      color: #B7BDC6;
    }

    .status-indicator {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #5E6673;
    }

    .status-indicator.active {
      background: #0ECB81;
      box-shadow: 0 0 8px rgba(14, 203, 129, 0.5);
    }

    .status-text {
      font-weight: 600;
      color: #0ECB81;
    }

    .update-time {
      color: #5E6673;
      margin-left: 4px;
    }

    /* Scrollbar styling */
    .market-ticker-bar::-webkit-scrollbar {
      height: 4px;
    }

    .market-ticker-bar::-webkit-scrollbar-track {
      background: #1E2026;
    }

    .market-ticker-bar::-webkit-scrollbar-thumb {
      background: #2B2F36;
      border-radius: 2px;
    }

    .market-ticker-bar::-webkit-scrollbar-thumb:hover {
      background: #5E6673;
    }

    @media (max-width: 768px) {
      .ticker-volume {
        display: none;
      }

      .ticker-container {
        gap: 12px;
      }
    }
  `]
})
export class MarketTickerComponent implements OnInit, OnDestroy {
  tickers: CryptoPrice[] = [];
  lastUpdate: string | null = null;
  isLive: boolean = false;
  private subscription?: Subscription;

  constructor(
    private marketDataService: MarketDataService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Subscribe to market data updates
    this.subscription = this.marketDataService.prices$.subscribe(data => {
      if (data && data.prices) {
        this.updateTickers(data);
        this.lastUpdate = data.last_update || null;
        this.isLive = true;
      }
    });
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  private updateTickers(data: MarketDataResponse): void {
    // Extract prices in order: BTC, ETH, LTC, SOL, DOGE
    const symbolOrder = ['BTC-USD', 'ETH-USD', 'LTC-USD', 'SOL-USD', 'DOGE-USD'];
    this.tickers = symbolOrder
      .map(symbol => data.prices[symbol])
      .filter(ticker => ticker !== undefined);
  }

  formatPrice(price: number): string {
    if (price >= 1000) {
      return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else if (price >= 1) {
      return `$${price.toFixed(2)}`;
    } else {
      return `$${price.toFixed(4)}`;
    }
  }

  formatVolume(volume: number): string {
    if (volume >= 1000000000) {
      return `${(volume / 1000000000).toFixed(2)}B`;
    } else if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(2)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(2)}K`;
    }
    return volume.toFixed(0);
  }

  getTimeAgo(timestamp: string): string {
    const now = new Date().getTime();
    const update = new Date(timestamp).getTime();
    const seconds = Math.floor((now - update) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  }

  navigateToTrade(symbol: string): void {
    // Navigate to trading page for the selected pair
    this.router.navigate(['/trading', symbol]);
  }
}
