import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { MarketDataService, MarketDataResponse } from '../../../../core/services/market-data.service';

@Component({
  selector: 'app-market-data',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './market-data.component.html',
  styleUrls: ['./market-data.component.scss']
})
export class MarketDataComponent {
  public marketData$: Observable<MarketDataResponse | null>;

  constructor(private marketDataService: MarketDataService) {
    this.marketData$ = this.marketDataService.prices$;
  }
}
