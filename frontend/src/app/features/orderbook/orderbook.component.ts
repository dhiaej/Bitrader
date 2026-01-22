import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { OrderbookService, Order, OrderBookData } from '../../core/services/orderbook.service';
import { WalletService } from '../../core/services/wallet.service';
import { MarketDataService, MarketDataResponse } from '../../core/services/market-data.service';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-orderbook',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './orderbook.component.html',
  styleUrls: ['./orderbook.component.scss']
})
export class OrderbookComponent implements OnInit, OnDestroy {
  orderForm: FormGroup;
  orderBook: OrderBookData | null = null;
  myOrders: Order[] = [];
  selectedInstrument = 'BTC/USD';
  orderType: 'BUY' | 'SELL' = 'BUY';
  orderSubtype: 'LIMIT' | 'MARKET' = 'LIMIT';
  isLoading = false;
  errorMessage = '';
  successMessage = '';
  private destroy$ = new Subject<void>();
  currentPrices: MarketDataResponse | null = null;

  instruments = [
    'BTC/USD', 'BTC/USDT', 'ETH/USD', 'ETH/USDT',
    'BNB/USD', 'BNB/USDT', 'XRP/USD', 'XRP/USDT',
    'ADA/USD', 'ADA/USDT', 'SOL/USD', 'SOL/USDT',
    'DOGE/USD', 'DOGE/USDT', 'DOT/USD', 'DOT/USDT',
    'MATIC/USD', 'MATIC/USDT', 'AVAX/USD', 'AVAX/USDT',
    'LINK/USD', 'LINK/USDT', 'UNI/USD', 'UNI/USDT',
    'ATOM/USD', 'ATOM/USDT', 'LTC/USD', 'LTC/USDT',
    'SHIB/USD', 'SHIB/USDT', 'TRX/USD', 'TRX/USDT',
    'ARB/USD', 'ARB/USDT', 'OP/USD', 'OP/USDT'
  ];

  // Orderbook settings
  priceGrouping = 0.01; // Default grouping
  depthLimit = 15; // Default depth

  constructor(
    private fb: FormBuilder,
    private orderbookService: OrderbookService,
    private walletService: WalletService,
    private marketDataService: MarketDataService
  ) {
    this.orderForm = this.fb.group({
      price: ['', [Validators.required, Validators.min(0.01)]],
      quantity: ['', [Validators.required, Validators.min(0.00000001)]]
    });
  }

  ngOnInit(): void {
    this.loadOrderBook();
    this.loadMyOrders();

    // Subscribe to real-time price updates
    this.marketDataService.prices$.subscribe(prices => {
      this.currentPrices = prices;
      // Auto-update price field with real-time data
      if (prices && this.orderSubtype === 'LIMIT') {
        this.updatePriceFromMarket();
      }
    });

    // Auto-refresh order book every 5 seconds
    setInterval(() => this.loadOrderBook(), 5000);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadOrderBook(): void {
    this.orderbookService.getOrderBook(this.selectedInstrument, this.depthLimit)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.orderBook = data;
          if (this.orderSubtype === 'LIMIT' && data.last_price) {
            this.orderForm.patchValue({ price: parseFloat(data.last_price) });
          }
        },
        error: (error) => console.error('Error loading order book:', error)
      });
  }

  loadMyOrders(): void {
    this.orderbookService.loadMyOrders();
    this.orderbookService.orders$
      .pipe(takeUntil(this.destroy$))
      .subscribe(orders => {
        this.myOrders = orders.filter(o => o.instrument === this.selectedInstrument);
      });
  }

  onInstrumentChange(instrument: string): void {
    this.selectedInstrument = instrument;
    this.loadOrderBook();
    this.loadMyOrders();
  }

  setOrderType(type: 'BUY' | 'SELL'): void {
    this.orderType = type;
  }

  setOrderSubtype(subtype: 'LIMIT' | 'MARKET'): void {
    this.orderSubtype = subtype;
    if (subtype === 'MARKET') {
      this.orderForm.get('price')?.disable();
    } else {
      this.orderForm.get('price')?.enable();
    }
  }

  onSubmit(): void {
    if (this.orderForm.invalid && this.orderSubtype === 'LIMIT') {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    const order: Order = {
      instrument: this.selectedInstrument,
      order_type: this.orderType,
      order_subtype: this.orderSubtype,
      quantity: this.orderForm.value.quantity
    };

    if (this.orderSubtype === 'LIMIT') {
      order.price = this.orderForm.value.price;
    }

    this.orderbookService.placeOrder(order).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.successMessage = `Order placed successfully! ID: ${response.id}`;
        this.orderForm.reset();
        this.loadOrderBook();
        this.loadMyOrders();
        this.walletService.loadWallets();

        setTimeout(() => this.successMessage = '', 5000);
      },
      error: (error) => {
        this.isLoading = false;
        this.errorMessage = error.error?.detail || 'Failed to place order';
      }
    });
  }

  cancelOrder(orderId: number): void {
    if (!confirm('Are you sure you want to cancel this order?')) {
      return;
    }

    this.orderbookService.cancelOrder(orderId).subscribe({
      next: () => {
        this.successMessage = 'Order cancelled successfully';
        this.loadMyOrders();
        this.walletService.loadWallets();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Failed to cancel order';
      }
    });
  }

  formatPrice(price: number | string): string {
    return parseFloat(price.toString()).toFixed(2);
  }

  formatQuantity(quantity: number | string): string {
    return parseFloat(quantity.toString()).toFixed(8);
  }

  calculateTotal(): number {
    const price = this.orderForm.value.price || 0;
    const quantity = this.orderForm.value.quantity || 0;
    return price * quantity;
  }

  updatePriceFromMarket(): void {
    if (!this.currentPrices) return;

    const symbol = this.selectedInstrument.replace('/', '-');
    const priceData = this.currentPrices.prices[symbol];

    if (priceData && this.orderSubtype === 'LIMIT') {
      this.orderForm.patchValue({
        price: priceData.price.toFixed(2)
      });
    }
  }

  getCurrentMarketPrice(): number | null {
    if (!this.currentPrices) return null;
    const symbol = this.selectedInstrument.replace('/', '-');
    const priceData = this.currentPrices.prices[symbol];
    return priceData ? priceData.price : null;
  }

  // Calculate cumulative sum for Sum column
  getCumulativeSum(orders: any[], index: number): number {
    let sum = 0;
    for (let i = 0; i <= index; i++) {
      sum += orders[i].price * orders[i].quantity;
    }
    return sum;
  }

  // Fill order form when clicking on a price
  fillOrderForm(type: 'BUY' | 'SELL', price: number): void {
    this.orderType = type;
    if (this.orderSubtype === 'LIMIT') {
      this.orderForm.patchValue({ price: parseFloat(price.toFixed(2)) });
    }
  }
}
