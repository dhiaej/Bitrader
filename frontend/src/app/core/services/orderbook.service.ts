import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';

export interface Order {
  id?: number;
  user_id?: number;
  instrument: string;
  order_type: 'BUY' | 'SELL';
  order_subtype: 'LIMIT' | 'MARKET';
  price?: number;
  quantity: number;
  remaining_quantity?: number;
  status?: string;
  created_at?: string;
}

export interface Trade {
  id: number;
  buy_order_id: number;
  sell_order_id: number;
  buyer_id: number;
  seller_id: number;
  instrument: string;
  quantity: string;
  price: string;
  buyer_fee: string;
  seller_fee: string;
  created_at: string;
}

export interface OrderBookData {
  instrument: string;
  bids: Array<{ price: number; quantity: number; count: number }>;
  asks: Array<{ price: number; quantity: number; count: number }>;
  last_price: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class OrderbookService {
  private ordersSubject = new BehaviorSubject<Order[]>([]);
  public orders$ = this.ordersSubject.asObservable();

  private tradesSubject = new BehaviorSubject<Trade[]>([]);
  public trades$ = this.tradesSubject.asObservable();

  private orderBookSubject = new BehaviorSubject<OrderBookData | null>(null);
  public orderBook$ = this.orderBookSubject.asObservable();

  constructor(private api: ApiService) {}

  placeOrder(order: Order): Observable<Order> {
    return this.api.post<Order>('/orderbook/orders', order).pipe(
      tap(() => {
        this.loadMyOrders();
        this.loadOrderBook(order.instrument);
      })
    );
  }

  loadMyOrders(): void {
    this.api.get<Order[]>('/orderbook/orders').subscribe({
      next: (orders) => this.ordersSubject.next(orders),
      error: (error) => console.error('Error loading orders:', error)
    });
  }

  cancelOrder(orderId: number): Observable<any> {
    return this.api.delete(`/orderbook/orders/${orderId}`).pipe(
      tap(() => this.loadMyOrders())
    );
  }

  loadOrderBook(instrument: string, depth: number = 20): void {
    this.api.get<OrderBookData>(`/orderbook?instrument=${encodeURIComponent(instrument)}&depth=${depth}`)
      .subscribe({
        next: (data) => this.orderBookSubject.next(data),
        error: (error) => console.error('Error loading order book:', error)
      });
  }

  getOrderBook(instrument: string, depth: number = 20): Observable<OrderBookData> {
    return this.api.get<OrderBookData>(`/orderbook?instrument=${encodeURIComponent(instrument)}&depth=${depth}`).pipe(
      tap(data => this.orderBookSubject.next(data))
    );
  }

  loadTrades(): void {
    this.api.get<Trade[]>('/orderbook/trades').subscribe({
      next: (trades) => this.tradesSubject.next(trades),
      error: (error) => console.error('Error loading trades:', error)
    });
  }

  getInstrumentPrice(instrument: string): number {
    const orderBook = this.orderBookSubject.value;
    if (orderBook && orderBook.last_price) {
      return parseFloat(orderBook.last_price);
    }
    return 0;
  }
}
