import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Observable } from 'rxjs';
import { MarketDataService, MarketDataResponse } from '../../../../core/services/market-data.service';

@Component({
  selector: 'app-pair-switcher',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './pair-switcher.component.html',
  styleUrls: ['./pair-switcher.component.scss']
})
export class PairSwitcherComponent {
  public marketData$: Observable<MarketDataResponse | null>;

  constructor(
    private marketDataService: MarketDataService,
    private router: Router
  ) {
    this.marketData$ = this.marketDataService.prices$;
  }

  navigateToPair(symbol: string): void {
    this.router.navigate(['/trade', symbol]);
  }
}
