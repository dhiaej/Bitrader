import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { trigger, transition, style, animate } from '@angular/animations';
import { AuthService, User } from '../../core/services/auth.service';
import { WalletService, Wallet } from '../../core/services/wallet.service';
import { MarketDataService, MarketDataResponse } from '../../core/services/market-data.service';
import { PricePredictionService, AllPredictions, PricePrediction } from '../../core/services/price-prediction.service';
import { AiChatWidgetComponent } from '../../shared/components/ai-chat-widget/ai-chat-widget.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, AiChatWidgetComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.95)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'scale(1)' }))
      ]),
      transition(':leave', [
        animate('150ms ease-in', style({ opacity: 0, transform: 'scale(0.95)' }))
      ])
    ])
  ]
})
export class DashboardComponent implements OnInit {
  currentUser: User | null = null;
  wallets: Wallet[] = [];
  totalBalanceUSD = 0;
  isLoading = true;
  currentPrices: MarketDataResponse | null = null;
  predictions: AllPredictions | null = null;
  showBTCPrediction = false;
  showETHPrediction = false;
  activePrediction: (PricePrediction & { symbol: string }) | null = null;

  // All supported cryptocurrencies
  cryptocurrencies = [
    { symbol: 'BTC', name: 'Bitcoin', icon: '₿', iconClass: 'btc' },
    { symbol: 'ETH', name: 'Ethereum', icon: 'Ξ', iconClass: 'eth' },
    { symbol: 'BNB', name: 'Binance Coin', icon: '🔶', iconClass: 'bnb' },
    { symbol: 'XRP', name: 'Ripple', icon: '💧', iconClass: 'xrp' },
    { symbol: 'ADA', name: 'Cardano', icon: '🔷', iconClass: 'ada' },
    { symbol: 'SOL', name: 'Solana', icon: '◎', iconClass: 'sol' },
    { symbol: 'DOGE', name: 'Dogecoin', icon: 'Ð', iconClass: 'doge' },
    { symbol: 'DOT', name: 'Polkadot', icon: '●', iconClass: 'dot' },
    { symbol: 'MATIC', name: 'Polygon', icon: '⬡', iconClass: 'matic' },
    { symbol: 'AVAX', name: 'Avalanche', icon: '🔺', iconClass: 'avax' },
    { symbol: 'LINK', name: 'Chainlink', icon: '🔗', iconClass: 'link' },
    { symbol: 'UNI', name: 'Uniswap', icon: '🦄', iconClass: 'uni' },
    { symbol: 'ATOM', name: 'Cosmos', icon: '⚛', iconClass: 'atom' },
    { symbol: 'LTC', name: 'Litecoin', icon: 'Ł', iconClass: 'ltc' },
    { symbol: 'SHIB', name: 'Shiba Inu', icon: '🐕', iconClass: 'shib' },
    { symbol: 'TRX', name: 'TRON', icon: '▲', iconClass: 'trx' },
    { symbol: 'ARB', name: 'Arbitrum', icon: '🔵', iconClass: 'arb' },
    { symbol: 'OP', name: 'Optimism', icon: '🔴', iconClass: 'op' }
  ];

  // Show more altcoins functionality
  showAllCryptos = false;
  searchQuery = '';

  constructor(
    private authService: AuthService,
    private walletService: WalletService,
    private marketDataService: MarketDataService,
    private predictionService: PricePredictionService
  ) {}

  ngOnInit(): void {
    this.loadUserData();
    this.loadWallets();
    this.loadPredictions();

    // Subscribe to real-time price updates
    this.marketDataService.prices$.subscribe(prices => {
      this.currentPrices = prices;
    });

    // Subscribe to prediction updates
    this.predictionService.predictions$.subscribe(predictions => {
      this.predictions = predictions;
    });
  }

  loadUserData(): void {
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });
  }

  loadWallets(): void {
    this.walletService.getWallets().subscribe({
      next: (wallets) => {
        this.wallets = wallets;
        this.totalBalanceUSD = this.walletService.getTotalBalanceUSD();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading wallets:', error);
        this.isLoading = false;
      }
    });
  }

  loadPredictions(): void {
    // Use cached predictions on initial load for faster performance
    this.predictionService.loadPredictions(false).subscribe({
      next: () => {
        console.log('Predictions loaded successfully');
      },
      error: (error) => {
        console.error('Error loading predictions:', error);
      }
    });
  }

  logout(): void {
    this.authService.logout();
  }

  formatBalance(balance: string): string {
    return parseFloat(balance).toFixed(8);
  }

  formatUSD(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  }

  getCryptoPrice(symbol: string): number {
    if (!this.currentPrices || !this.currentPrices.prices) return 0;
    const priceData = this.currentPrices.prices[`${symbol}-USD`];
    return priceData ? priceData.price : 0;
  }

  getCryptoPriceChange(symbol: string): number {
    if (!this.currentPrices || !this.currentPrices.prices) return 0;
    const priceData = this.currentPrices.prices[`${symbol}-USD`];
    return priceData ? priceData.change_percent : 0;
  }

  getCryptoVolume(symbol: string): number {
    if (!this.currentPrices || !this.currentPrices.prices) return 0;
    const priceData = this.currentPrices.prices[`${symbol}-USD`];
    return priceData ? priceData.volume : 0;
  }

  getCryptoMarketCap(symbol: string): number {
    if (!this.currentPrices || !this.currentPrices.prices) return 0;
    const priceData = this.currentPrices.prices[`${symbol}-USD`];
    return priceData ? priceData.market_cap : 0;
  }

  getDataSource(): string {
    return this.currentPrices?.active_source || 'Loading...';
  }

  formatLargeNumber(num: number): string {
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(2);
  }

  isPricePositive(symbol: string): boolean {
    return this.getCryptoPriceChange(symbol) >= 0;
  }

  // Prediction helper methods
  getPredictionBadge(symbol: string, timeframe: '1h' | '24h' | '7d') {
    if (!this.predictions || !this.predictions[symbol as 'BTC' | 'ETH']) {
      return { text: '', class: '', icon: '', show: false };
    }
    const prediction = this.predictions[symbol as 'BTC' | 'ETH'][timeframe];
    return this.predictionService.getPredictionBadge(prediction);
  }

  getPrediction(symbol: string, timeframe: '1h' | '24h' | '7d') {
    if (!this.predictions || !this.predictions[symbol as 'BTC' | 'ETH']) {
      return null;
    }
    return this.predictions[symbol as 'BTC' | 'ETH'][timeframe];
  }

  getRecommendationStyle(recommendation: string) {
    return this.predictionService.getRecommendationStyle(recommendation);
  }

  getTechSignalClass(signal: string): string {
    const signalLower = signal?.toLowerCase() || '';
    if (signalLower.includes('overbought') || signalLower.includes('bearish')) {
      return 'bearish';
    } else if (signalLower.includes('oversold') || signalLower.includes('bullish')) {
      return 'bullish';
    }
    return 'neutral';
  }

  toggleBTCPrediction() {
    const prediction = this.getPrediction('BTC', '24h');
    if (prediction) {
      this.activePrediction = { ...prediction, symbol: 'BTC' };
    }
  }

  toggleETHPrediction() {
    const prediction = this.getPrediction('ETH', '24h');
    if (prediction) {
      this.activePrediction = { ...prediction, symbol: 'ETH' };
    }
  }

  togglePrediction(symbol: string) {
    const prediction = this.getPrediction(symbol, '24h');
    if (prediction) {
      this.activePrediction = { ...prediction, symbol };
    }
  }

  closeModal() {
    this.activePrediction = null;
  }

  // Get filtered cryptocurrencies based on search and show all toggle
  getDisplayedCryptos() {
    let filtered = this.cryptocurrencies;

    // Apply search filter
    if (this.searchQuery.trim()) {
      const query = this.searchQuery.toLowerCase();
      filtered = filtered.filter(crypto =>
        crypto.symbol.toLowerCase().includes(query) ||
        crypto.name.toLowerCase().includes(query)
      );
    }

    // If not showing all, only return BTC and ETH (unless search is active)
    if (!this.showAllCryptos && !this.searchQuery.trim()) {
      return filtered.filter(crypto => crypto.symbol === 'BTC' || crypto.symbol === 'ETH');
    }

    return filtered;
  }

  // Get count of hidden cryptos
  getHiddenCryptosCount() {
    return this.cryptocurrencies.length - 2; // All except BTC and ETH
  }

  // Toggle show all cryptos
  toggleShowAllCryptos() {
    this.showAllCryptos = !this.showAllCryptos;
  }
}
