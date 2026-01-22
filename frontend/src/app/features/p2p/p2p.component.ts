import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { P2pService, P2PAdvertisement, P2PTrade, P2PNotification } from '../../core/services/p2p.service';
import { WalletService } from '../../core/services/wallet.service';
import { MarketDataService, MarketDataResponse } from '../../core/services/market-data.service';
import { DisputeService } from '../../core/services/dispute.service';

@Component({
  selector: 'app-p2p',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './p2p.component.html',
  styleUrls: ['./p2p.component.scss'],
  animations: [
    trigger('slideDown', [
      transition(':enter', [
        style({ height: '0', opacity: 0, overflow: 'hidden' }),
        animate('400ms ease-out', style({ height: '*', opacity: 1 }))
      ]),
      transition(':leave', [
        style({ height: '*', opacity: 1, overflow: 'hidden' }),
        animate('300ms ease-in', style({ height: '0', opacity: 0 }))
      ])
    ])
  ]
})
export class P2pComponent implements OnInit {
  advertisements: P2PAdvertisement[] = [];
  filteredAdvertisements: P2PAdvertisement[] = [];
  myTrades: P2PTrade[] = [];
  notifications: P2PNotification[] = [];
  unreadNotificationsCount = 0;
  showNotifications = false;
  showCreateAdForm = false;
  createAdForm: FormGroup;
  initiateTradeForm: FormGroup;
  selectedAd: P2PAdvertisement | null = null;
  showTradeModal = false;
  showInfoModal = false;
  showStrategiesGuide = false;
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  // Filter options
  filterAdType: string = 'ALL';
  filterCurrency: string = 'ALL';
  filterPaymentMethod: string = 'ALL';
  filterIsActive: string = 'ACTIVE';
  searchTerm: string = '';

  currencies = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE', 'DOT', 'MATIC', 'AVAX', 'LINK', 'UNI', 'ATOM', 'LTC', 'SHIB', 'TRX', 'ARB', 'OP', 'USDT'];
  fiatCurrencies = ['USD', 'EUR', 'GBP'];
  paymentMethods = ['Bank Transfer', 'PayPal', 'Wise', 'Revolut', 'Venmo', 'Zelle', 'Cash App', 'Western Union', 'MoneyGram', 'N26'];
  selectedPaymentMethods: string[] = [];
  currentPrices: MarketDataResponse | null = null;

  // Dispute management
  showDisputeModal = false;
  selectedTradeForDispute: P2PTrade | null = null;
  disputeReason = '';
  filingDispute = false;

  constructor(
    private fb: FormBuilder,
    private p2pService: P2pService,
    private walletService: WalletService,
    private marketDataService: MarketDataService,
    private disputeService: DisputeService
  ) {
    this.createAdForm = this.fb.group({
      ad_type: ['SELL', Validators.required],
      currency: ['BTC', Validators.required],
      fiat_currency: ['USD', Validators.required],
      price: ['', [Validators.required, Validators.min(0)]],
      min_limit: ['', [Validators.required, Validators.min(0)]],
      max_limit: ['', [Validators.required, Validators.min(0)]],
      available_amount: ['', [Validators.required, Validators.min(0)]],
      payment_methods: [['Bank Transfer'], Validators.required],
      payment_time_limit: [30, [Validators.required, Validators.min(5)]],
      terms_conditions: ['']
    });

    this.initiateTradeForm = this.fb.group({
      amount: ['', [Validators.required, Validators.min(0)]],
      payment_method: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.loadAdvertisements();
    this.loadMyTrades();
    this.loadNotifications();

    // Subscribe to real-time price updates
    this.marketDataService.prices$.subscribe(prices => {
      this.currentPrices = prices;
      // Auto-fill current market price when creating ad
      if (prices && this.showCreateAdForm) {
        this.updatePriceFromMarket();
      }
    });
  }

  loadAdvertisements(): void {
    // Build query params based on filters
    const params: any = {};

    if (this.filterIsActive === 'ACTIVE') {
      params.is_active = true;
    } else if (this.filterIsActive === 'INACTIVE') {
      params.is_active = false;
    }
    // If 'ALL', don't add is_active param to get everything

    if (this.searchTerm) {
      params.search = this.searchTerm;
    }

    this.p2pService.getAdvertisements(params).subscribe({
      next: (ads) => {
        this.advertisements = ads;
        this.applyFilters();
      },
      error: (error) => console.error('Error loading ads:', error)
    });
  }

  applyFilters(): void {
    // Apply client-side filters to the loaded advertisements
    let filtered = [...this.advertisements];

    // Filter by ad type
    if (this.filterAdType !== 'ALL') {
      filtered = filtered.filter(ad => ad.ad_type === this.filterAdType);
    }

    // Filter by currency
    if (this.filterCurrency !== 'ALL') {
      filtered = filtered.filter(ad => ad.currency === this.filterCurrency);
    }

    // Filter by payment method
    if (this.filterPaymentMethod !== 'ALL') {
      filtered = filtered.filter(ad =>
        ad.payment_methods.includes(this.filterPaymentMethod)
      );
    }

    this.filteredAdvertisements = filtered;
  }

  onFilterChange(): void {
    // Reload data from API when active/inactive filter or search changes
    this.loadAdvertisements();
  }

  toggleInfoModal(): void {
    this.showInfoModal = !this.showInfoModal;
  }

  toggleStrategiesGuide(): void {
    this.showStrategiesGuide = !this.showStrategiesGuide;
  }

  loadMyTrades(): void {
    this.p2pService.loadMyTrades();
    this.p2pService.trades$.subscribe(trades => {
      this.myTrades = trades;
    });
  }

  toggleCreateAdForm(): void {
    this.showCreateAdForm = !this.showCreateAdForm;
    if (this.showCreateAdForm) {
      this.selectedPaymentMethods = ['Bank Transfer'];
      this.createAdForm.reset({
        ad_type: 'SELL',
        currency: 'BTC',
        fiat_currency: 'USD',
        payment_time_limit: 30,
        payment_methods: ['Bank Transfer']
      });
      this.updatePriceFromMarket();
    } else {
      this.selectedPaymentMethods = [];
    }
  }

  updatePriceFromMarket(): void {
    const currency = this.createAdForm.get('currency')?.value;
    const fiatCurrency = this.createAdForm.get('fiat_currency')?.value;

    if (currency && fiatCurrency && this.currentPrices) {
      const symbol = `${currency}-${fiatCurrency}`;
      const priceData = this.currentPrices.prices[symbol];

      if (priceData) {
        this.createAdForm.patchValue({
          price: priceData.price.toFixed(2)
        });
      }
    }
  }

  getRealTimePrice(currency: string, fiatCurrency: string): number | null {
    if (!this.currentPrices) return null;
    const symbol = `${currency}-${fiatCurrency}`;
    const priceData = this.currentPrices.prices[symbol];
    return priceData ? priceData.price : null;
  }

  togglePaymentMethod(event: any, method: string): void {
    if (event.target.checked) {
      if (!this.selectedPaymentMethods.includes(method)) {
        this.selectedPaymentMethods.push(method);
      }
    } else {
      const index = this.selectedPaymentMethods.indexOf(method);
      if (index > -1) {
        this.selectedPaymentMethods.splice(index, 1);
      }
    }
    this.createAdForm.patchValue({
      payment_methods: this.selectedPaymentMethods
    });
  }

  getSelectedPaymentMethodsCount(): number {
    return this.selectedPaymentMethods.length;
  }

  onCreateAd(): void {
    if (this.createAdForm.invalid) return;

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.p2pService.createAdvertisement(this.createAdForm.value).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Advertisement created successfully! Checking for auto-matches...';
        this.showCreateAdForm = false;
        this.loadAdvertisements();
        this.loadNotifications(); // Reload notifications to check for auto-matches
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.isLoading = false;
        this.errorMessage = error.error?.detail || 'Failed to create advertisement';
      }
    });
  }

  openTradeModal(ad: P2PAdvertisement): void {
    this.selectedAd = ad;
    this.showTradeModal = true;
    this.initiateTradeForm.patchValue({
      payment_method: ad.payment_methods[0]
    });
  }

  closeTradeModal(): void {
    this.showTradeModal = false;
    this.selectedAd = null;
    this.initiateTradeForm.reset();
  }

  onInitiateTrade(): void {
    if (!this.selectedAd || this.initiateTradeForm.invalid) return;

    this.isLoading = true;
    this.errorMessage = '';

    const tradeData = {
      advertisement_id: this.selectedAd.id,
      ...this.initiateTradeForm.value
    };

    this.p2pService.initiateTrade(tradeData).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Trade initiated successfully!';
        this.closeTradeModal();
        this.loadMyTrades();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.isLoading = false;
        this.errorMessage = error.error?.detail || 'Failed to initiate trade';
      }
    });
  }

  markPaymentSent(tradeId: number): void {
    this.p2pService.markPaymentSent(tradeId).subscribe({
      next: () => {
        this.successMessage = 'Payment marked as sent!';
        this.loadMyTrades();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Action failed';
      }
    });
  }

  confirmPayment(tradeId: number): void {
    if (!confirm('Are you sure you received the payment? This will release the crypto.')) return;

    this.p2pService.confirmPayment(tradeId).subscribe({
      next: () => {
        this.successMessage = 'Payment confirmed! Trade completed.';
        this.loadMyTrades();
        this.walletService.loadWallets();
        this.walletService.getTransactionHistory().subscribe();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Action failed';
      }
    });
  }

  cancelTrade(tradeId: number): void {
    if (!confirm('Are you sure you want to cancel this trade?')) return;

    this.p2pService.cancelTrade(tradeId).subscribe({
      next: () => {
        this.successMessage = 'Trade cancelled successfully!';
        this.loadMyTrades();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Action failed';
      }
    });
  }

  formatPrice(price: string | number): string {
    return parseFloat(price.toString()).toFixed(2);
  }

  formatAmount(amount: string | number): string {
    return parseFloat(amount.toString()).toFixed(8);
  }

  getTradeTypeLabel(ad: P2PAdvertisement): string {
    return ad.ad_type === 'SELL' ? 'Buy' : 'Sell';
  }

  getAdTypeColor(adType: string): string {
    return adType === 'BUY' ? '#02C076' : '#F6465D';
  }

  calculateTotal(): number {
    // Returns the fiat amount entered by user
    if (!this.selectedAd || !this.initiateTradeForm.value.amount) {
      return 0;
    }
    return parseFloat(this.initiateTradeForm.value.amount);
  }

  calculateCryptoAmount(): number {
    // Calculate how much crypto user will receive/send
    if (!this.selectedAd || !this.initiateTradeForm.value.amount) {
      return 0;
    }
    const fiatAmount = parseFloat(this.initiateTradeForm.value.amount);
    const price = parseFloat(this.selectedAd.price);
    return fiatAmount / price;
  }

  loadNotifications(): void {
    this.p2pService.getNotifications().subscribe({
      next: (notifications) => {
        this.notifications = notifications;
        this.unreadNotificationsCount = notifications.filter(n => !n.is_read).length;
      },
      error: (error) => console.error('Error loading notifications:', error)
    });
  }

  toggleNotifications(): void {
    this.showNotifications = !this.showNotifications;
  }

  markNotificationAsRead(notification: P2PNotification): void {
    if (notification.is_read) return;

    this.p2pService.markNotificationRead(notification.id).subscribe({
      next: () => {
        notification.is_read = true;
        this.unreadNotificationsCount--;
      },
      error: (error) => console.error('Error marking notification as read:', error)
    });
  }

  acceptPartialMatch(notification: P2PNotification): void {
    if (!notification.data) return;

    const { your_ad_id, match_ad_id, match_amount } = notification.data;

    if (confirm(`Accept partial match of ${match_amount} crypto?`)) {
      this.p2pService.acceptPartialMatch(your_ad_id, match_ad_id, parseFloat(match_amount)).subscribe({
        next: (response) => {
          this.successMessage = 'Partial match accepted! Trade created.';
          this.loadNotifications();
          this.loadMyTrades();
          this.loadAdvertisements();
          setTimeout(() => this.successMessage = '', 3000);
        },
        error: (error) => {
          this.errorMessage = error.error?.detail || 'Failed to accept partial match';
        }
      });
    }
  }

  getNotificationIcon(type: string): string {
    switch (type) {
      case 'P2P_MATCH':
        return '🎉';
      case 'PARTIAL_MATCH':
        return '';
      default:
        return '📢';
    }
  }

  formatNotificationTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }

  getCryptoPrice(symbol: string): number {
    if (!this.currentPrices || !this.currentPrices.prices) return 0;
    const priceData = this.currentPrices.prices[`${symbol}-USD`];
    return priceData ? priceData.price : 0;
  }

  // Statistics calculations
  getStatistics() {
    const activeAds = this.advertisements.filter(ad => ad.is_active && parseFloat(ad.available_amount) > 0);
    console.log('Statistics - Total advertisements:', this.advertisements.length);
    console.log('Statistics - Active ads:', activeAds.length);

    const buyAds = activeAds.filter(ad => ad.ad_type === 'BUY').length;
    const sellAds = activeAds.filter(ad => ad.ad_type === 'SELL').length;

    // Calculate total volume (sum of available_amount * price)
    const totalVolume = activeAds.reduce((sum, ad) => {
      return sum + (parseFloat(ad.available_amount) * parseFloat(ad.price));
    }, 0);

    // Get most traded currency
    const mostTradedCurrency = this.getMostTradedCurrency();
    const currencyAds = activeAds.filter(ad => ad.currency === mostTradedCurrency);

    // Calculate average price for most traded currency
    const averagePrice = currencyAds.length > 0
      ? currencyAds.reduce((sum, ad) => sum + parseFloat(ad.price), 0) / currencyAds.length
      : 0;

    // Calculate price difference vs market price
    let priceChange = 0;
    if (this.currentPrices && mostTradedCurrency && averagePrice > 0) {
      const marketPrice = this.getCryptoPrice(mostTradedCurrency);
      if (marketPrice > 0) {
        priceChange = ((averagePrice - marketPrice) / marketPrice) * 100;
      }
    }

    // Count unique traders (unique user_ids)
    const uniqueTraders = new Set(activeAds.map(ad => ad.user_id)).size;

    // Simulate online traders (30-60% of active traders)
    const onlineNow = Math.floor(uniqueTraders * (0.3 + Math.random() * 0.3));

    // Count unique payment methods
    const allPaymentMethods = new Set<string>();
    activeAds.forEach(ad => {
      // payment_methods is already an array in the interface
      if (Array.isArray(ad.payment_methods)) {
        ad.payment_methods.forEach(method => allPaymentMethods.add(method));
      }
    });

    // Simulate response time (5-15 minutes average)
    const avgResponseTime = `${Math.floor(5 + Math.random() * 10)}min`;

    // Simulate completion rate (85-95%)
    const completionRate = Math.floor(85 + Math.random() * 10);

    return {
      totalAds: activeAds.length,
      buyAds,
      sellAds,
      totalVolume,
      averagePrice,
      priceChange,
      activeTraders: uniqueTraders,
      onlineNow,
      avgResponseTime,
      completionRate,
      paymentMethodsCount: allPaymentMethods.size
    };
  }

  getMostTradedCurrency(): string {
    const currencyCounts = this.advertisements.reduce((acc, ad) => {
      acc[ad.currency] = (acc[ad.currency] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    let maxCount = 0;
    let mostTraded = 'BTC';

    Object.entries(currencyCounts).forEach(([currency, count]) => {
      if (count > maxCount) {
        maxCount = count;
        mostTraded = currency;
      }
    });

    return mostTraded;
  }

  getMostPopularPayment(): string {
    const paymentCounts: Record<string, number> = {};

    this.advertisements.forEach(ad => {
      // payment_methods is already an array
      if (Array.isArray(ad.payment_methods)) {
        ad.payment_methods.forEach((method: string) => {
          paymentCounts[method] = (paymentCounts[method] || 0) + 1;
        });
      }
    });

    let maxCount = 0;
    let mostPopular = 'Bank Transfer';

    Object.entries(paymentCounts).forEach(([method, count]) => {
      if (count > maxCount) {
        maxCount = count;
        mostPopular = method;
      }
    });

    return mostPopular;
  }

  // Dispute Management Methods
  canFileDispute(trade: P2PTrade): boolean {
    // Can file dispute if trade is PAYMENT_SENT or DISPUTED
    return trade.status === 'PAYMENT_SENT' || trade.status === 'DISPUTED';
  }

  openDisputeModal(trade: P2PTrade): void {
    this.selectedTradeForDispute = trade;
    this.showDisputeModal = true;
    this.disputeReason = '';
    this.errorMessage = '';
    this.successMessage = '';
  }

  closeDisputeModal(): void {
    this.showDisputeModal = false;
    this.selectedTradeForDispute = null;
    this.disputeReason = '';
  }

  fileDispute(): void {
    if (!this.selectedTradeForDispute || !this.disputeReason.trim()) {
      this.errorMessage = 'Please provide a reason for the dispute';
      return;
    }

    this.filingDispute = true;
    this.errorMessage = '';

    this.disputeService.createDispute({
      trade_id: this.selectedTradeForDispute.id,
      reason: this.disputeReason
    }).subscribe({
      next: () => {
        this.successMessage = 'Dispute filed successfully! An admin will review it soon.';
        this.filingDispute = false;
        this.closeDisputeModal();
        this.loadMyTrades(); // Refresh trades to show DISPUTED status
        setTimeout(() => this.successMessage = '', 5000);
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Failed to file dispute';
        this.filingDispute = false;
      }
    });
  }

  getVolumeDistribution() {
    const distribution: { currency: string; volume: number; percent: number }[] = [];
    const currencies = ['BTC', 'ETH', 'USDT'];

    currencies.forEach(currency => {
      const ads = this.advertisements.filter(ad => ad.currency === currency && ad.is_active);
      const volume = ads.reduce((sum, ad) => sum + (parseFloat(ad.available_amount) * parseFloat(ad.price)), 0);
      distribution.push({ currency, volume, percent: 0 });
    });

    const totalVolume = distribution.reduce((sum, item) => sum + item.volume, 0);
    distribution.forEach(item => {
      item.percent = totalVolume > 0 ? (item.volume / totalVolume) * 100 : 0;
    });

    return distribution;
  }

  getCurrencyBreakdown() {
    const colors = { BTC: '#F7931A', ETH: '#627EEA', USDT: '#26A17B' };
    const distribution = this.getVolumeDistribution();

    return distribution.map(item => ({
      currency: item.currency,
      volume: item.volume,
      color: colors[item.currency as keyof typeof colors] || '#848E9C'
    }));
  }

  getTopPaymentMethods() {
    const paymentCounts: Record<string, number> = {};

    this.advertisements.forEach(ad => {
      if (Array.isArray(ad.payment_methods)) {
        ad.payment_methods.forEach((method: string) => {
          paymentCounts[method] = (paymentCounts[method] || 0) + 1;
        });
      }
    });

    const sorted = Object.entries(paymentCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    const maxCount = sorted[0]?.[1] || 1;

    return sorted.map(([name, count]) => ({
      name,
      count,
      percent: (count / maxCount) * 100
    }));
  }
}
