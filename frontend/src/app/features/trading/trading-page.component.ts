import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { Observable, Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { CandlestickChartComponent } from './components/candlestick-chart/candlestick-chart.component';
import { PairSwitcherComponent } from './components/pair-switcher/pair-switcher.component';
import { IndicatorAssistantComponent } from './components/indicator-assistant/indicator-assistant.component';
import { MarketDataService, CryptoPrice } from '../../core/services/market-data.service';

@Component({
  selector: 'app-trading-page',
  standalone: true,
  imports: [
    CommonModule,
    CandlestickChartComponent,
    PairSwitcherComponent,
    IndicatorAssistantComponent
  ],
  templateUrl: './trading-page.component.html',
  styleUrls: ['./trading-page.component.scss']
})
export class TradingPageComponent implements OnInit, OnDestroy {
  public symbol$!: Observable<string>;
  public currentPrice: number | null = null;
  public currentPriceData: CryptoPrice | null = null;
  private subscriptions: Subscription[] = [];
  private currentSymbol: string = '';

  constructor(
    private route: ActivatedRoute,
    private marketDataService: MarketDataService
  ) {}

  ngOnInit(): void {
    this.symbol$ = this.route.params.pipe(
      map(params => params['symbol'])
    );

    // Subscribe to symbol changes and update price
    const symbolSub = this.symbol$.subscribe(symbol => {
      this.currentSymbol = symbol;
      this.updateCurrentPrice();
    });
    this.subscriptions.push(symbolSub);

    // Subscribe to market data updates
    const priceSub = this.marketDataService.prices$.subscribe(data => {
      if (data && this.currentSymbol) {
        this.currentPriceData = data.prices[this.currentSymbol] || null;
        this.currentPrice = this.currentPriceData?.price || null;
      }
    });
    this.subscriptions.push(priceSub);
  }

  private updateCurrentPrice(): void {
    this.currentPrice = this.marketDataService.getCurrentPrice(this.currentSymbol);
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }
}
