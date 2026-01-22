import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap, map } from 'rxjs';
import { ApiService } from './api.service';

export interface P2PAdvertisement {
  id: number;
  user_id: number;
  ad_type: 'BUY' | 'SELL';
  currency: string;
  fiat_currency: string;
  price: string;
  min_limit: string;
  max_limit: string;
  available_amount: string;
  payment_methods: string[];
  payment_time_limit: number;
  terms_conditions?: string;
  is_active: boolean;
  created_at: string;
  user?: {
    username: string;
    reputation?: {
      rating: number;
      trades_count: number;
    };
  };
}

export interface P2PTrade {
  id: number;
  advertisement_id: number;
  buyer_id: number;
  seller_id: number;
  amount: string;
  price: string;
  total_fiat: string;
  currency: string;
  fiat_currency: string;
  payment_method: string;
  status: string;
  payment_deadline: string;
  created_at: string;
  advertisement?: P2PAdvertisement;
}

export interface CreateAdvertisementRequest {
  ad_type: 'BUY' | 'SELL';
  currency: string;
  fiat_currency: string;
  price: number;
  min_limit: number;
  max_limit: number;
  available_amount: number;
  payment_methods: string[];
  payment_time_limit: number;
  terms_conditions?: string;
}

export interface InitiateTradeRequest {
  advertisement_id: number;
  amount: number;
  payment_method: string;
}

export interface P2PNotification {
  id: number;
  type: string;
  title: string;
  message: string;
  data: any;
  is_read: boolean;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class P2pService {
  private advertisementsSubject = new BehaviorSubject<P2PAdvertisement[]>([]);
  public advertisements$ = this.advertisementsSubject.asObservable();

  private myAdsSubject = new BehaviorSubject<P2PAdvertisement[]>([]);
  public myAds$ = this.myAdsSubject.asObservable();

  private tradesSubject = new BehaviorSubject<P2PTrade[]>([]);
  public trades$ = this.tradesSubject.asObservable();

  constructor(private api: ApiService) {}

  createAdvertisement(data: CreateAdvertisementRequest): Observable<P2PAdvertisement> {
    return this.api.post<P2PAdvertisement>('/p2p/advertisements', data).pipe(
      tap(() => this.loadMyAdvertisements())
    );
  }

  getAdvertisements(params?: any): Observable<P2PAdvertisement[]> {
    let endpoint = '/p2p/advertisements';
    const queryParams: string[] = [];

    if (params) {
      // Handle all possible query parameters
      if (params.currency) queryParams.push(`currency=${params.currency}`);
      if (params.ad_type) queryParams.push(`ad_type=${params.ad_type}`);
      if (params.fiat_currency) queryParams.push(`fiat_currency=${params.fiat_currency}`);
      if (params.is_active !== undefined) queryParams.push(`is_active=${params.is_active}`);
      if (params.search) queryParams.push(`search=${encodeURIComponent(params.search)}`);
      if (params.min_amount) queryParams.push(`min_amount=${params.min_amount}`);
      if (params.max_amount) queryParams.push(`max_amount=${params.max_amount}`);
      if (params.limit) queryParams.push(`limit=${params.limit}`);
      if (params.offset) queryParams.push(`offset=${params.offset}`);
    }

    if (queryParams.length > 0) {
      endpoint += '?' + queryParams.join('&');
    }

    return this.api.get<any[]>(endpoint).pipe(
      map(ads => {
        // Parse payment_methods from JSON string to array
        const parsedAds = ads.map(ad => ({
          ...ad,
          payment_methods: typeof ad.payment_methods === 'string'
            ? JSON.parse(ad.payment_methods)
            : ad.payment_methods
        })) as P2PAdvertisement[];
        this.advertisementsSubject.next(parsedAds);
        return parsedAds;
      })
    );
  }

  loadMyAdvertisements(): void {
    this.api.get<any[]>('/p2p/my-advertisements').subscribe({
      next: (ads) => {
        // Parse payment_methods from JSON string to array
        const parsedAds = ads.map(ad => ({
          ...ad,
          payment_methods: typeof ad.payment_methods === 'string'
            ? JSON.parse(ad.payment_methods)
            : ad.payment_methods
        }));
        this.myAdsSubject.next(parsedAds);
      },
      error: (error) => console.error('Error loading my ads:', error)
    });
  }

  deleteAdvertisement(adId: number): Observable<any> {
    return this.api.delete(`/p2p/advertisements/${adId}`).pipe(
      tap(() => this.loadMyAdvertisements())
    );
  }

  initiateTrade(data: InitiateTradeRequest): Observable<P2PTrade> {
    return this.api.post<P2PTrade>('/p2p/trades', data).pipe(
      tap(() => this.loadMyTrades())
    );
  }

  loadMyTrades(): void {
    this.api.get<P2PTrade[]>('/p2p/trades').subscribe({
      next: (trades) => this.tradesSubject.next(trades),
      error: (error) => console.error('Error loading trades:', error)
    });
  }

  markPaymentSent(tradeId: number): Observable<any> {
    return this.api.post(`/p2p/trades/${tradeId}/payment-sent`, {}).pipe(
      tap(() => this.loadMyTrades())
    );
  }

  confirmPayment(tradeId: number): Observable<any> {
    return this.api.post(`/p2p/trades/${tradeId}/confirm-payment`, {}).pipe(
      tap(() => this.loadMyTrades())
    );
  }

  cancelTrade(tradeId: number): Observable<any> {
    return this.api.post(`/p2p/trades/${tradeId}/cancel`, {}).pipe(
      tap(() => this.loadMyTrades())
    );
  }

  getNotifications(unreadOnly: boolean = false): Observable<P2PNotification[]> {
    const params = unreadOnly ? '?unread_only=true' : '';
    return this.api.get<P2PNotification[]>(`/p2p/notifications${params}`);
  }

  markNotificationRead(notificationId: number): Observable<any> {
    return this.api.post(`/p2p/notifications/${notificationId}/read`, {});
  }

  acceptPartialMatch(adId: number, matchAdId: number, amount: number): Observable<any> {
    return this.api.post(`/p2p/partial-match/accept/${adId}`, {
      match_ad_id: matchAdId,
      amount: amount
    });
  }
}
