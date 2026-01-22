import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User } from './auth.service';
import { DisputeDetails } from './dispute.service';

export type { DisputeDetails };

export interface AdminStats {
  users: {
    total: number;
    active: number;
    verified: number;
    new_today: number;
    new_this_week: number;
  };
  trades: {
    orderbook_total: number;
    p2p_total: number;
    p2p_completed: number;
    p2p_completion_rate: number;
  };
  orders: {
    total: number;
    pending: number;
  };
  p2p_ads: {
    total: number;
    active: number;
  };
  disputes: {
    total: number;
    open: number;
  };
  financial: {
    total_transactions: number;
    total_volume_usd: number;
  };
  reputation: {
    avg_score: number;
    total_reviews: number;
  };
}

export interface UsersListResponse {
  total: number;
  skip: number;
  limit: number;
  users: User[];
}

export interface UserDetails {
  user: User;
  stats: {
    wallets: number;
    orders: number;
    p2p_ads: number;
    p2p_trades: number;
    reputation: {
      score: number;
      total_trades: number;
      completed_trades: number;
      average_rating: number;
    };
  };
}

export interface Trade {
  id: number;
  buyer_id: number;
  seller_id: number;
  instrument?: string;
  currency?: string;
  amount?: number;
  price: number;
  quantity?: number;
  total_amount?: number;
  status?: string;
  created_at: string;
}

export interface RecentTradesResponse {
  orderbook_trades: Trade[];
  p2p_trades: Trade[];
}

export interface Dispute {
  id: number;
  trade_id: number;
  filed_by: number;
  reason: string;
  status: string;
  created_at: string;
  resolved_at: string | null;
}

export interface DisputesListResponse {
  total: number;
  skip: number;
  limit: number;
  disputes: Dispute[];
}

export interface SuspiciousEvent {
  id: number;
  user_id: number;
  transaction_type: string;
  transaction_id: number | null;
  score: number;
  status: string;
  triggered_rules: string[];
  features: { [key: string]: any };
  explanation: string | null;
  admin_notes: string | null;
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: number | null;
}

export interface SuspiciousEventListResponse {
  total: number;
  skip: number;
  limit: number;
  events: SuspiciousEvent[];
}

export interface SuspiciousEventUpdatePayload {
  status?: string;
  admin_notes?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    });
  }

  getOverviewStats(): Observable<AdminStats> {
    return this.http.get<AdminStats>(`${this.apiUrl}/admin/stats/overview`, {
      headers: this.authHeaders()
    });
  }

  getUsers(skip = 0, limit = 20, search?: string, is_active?: boolean, is_admin?: boolean): Observable<UsersListResponse> {
    let params: any = { skip, limit };
    if (search) params.search = search;
    if (is_active !== undefined) params.is_active = is_active;
    if (is_admin !== undefined) params.is_admin = is_admin;

    return this.http.get<UsersListResponse>(`${this.apiUrl}/admin/users`, {
      headers: this.authHeaders(),
      params
    });
  }

  getUserDetails(userId: number): Observable<UserDetails> {
    return this.http.get<UserDetails>(`${this.apiUrl}/admin/users/${userId}`, {
      headers: this.authHeaders()
    });
  }

  toggleUserActive(userId: number): Observable<{ message: string; user: User }> {
    return this.http.put<{ message: string; user: User }>(
      `${this.apiUrl}/admin/users/${userId}/toggle-active`,
      {},
      { headers: this.authHeaders() }
    );
  }

  toggleUserAdmin(userId: number): Observable<{ message: string; user: User }> {
    return this.http.put<{ message: string; user: User }>(
      `${this.apiUrl}/admin/users/${userId}/toggle-admin`,
      {},
      { headers: this.authHeaders() }
    );
  }

  getRecentTrades(skip = 0, limit = 50): Observable<RecentTradesResponse> {
    return this.http.get<RecentTradesResponse>(`${this.apiUrl}/admin/trades/recent`, {
      headers: this.authHeaders(),
      params: { skip, limit }
    });
  }

  getDisputes(skip = 0, limit = 50, status?: string): Observable<DisputesListResponse> {
    let params: any = { skip, limit };
    if (status) params.status_filter = status;

    return this.http.get<DisputesListResponse>(`${this.apiUrl}/admin/disputes`, {
      headers: this.authHeaders(),
      params
    });
  }

  getSuspiciousEvents(
    skip = 0,
    limit = 50,
    status?: string,
    min_score?: number,
    transaction_type?: string,
    user_id?: number
  ): Observable<SuspiciousEventListResponse> {
    let params: any = { skip, limit };
    if (status) params.status = status;
    if (min_score !== undefined) params.min_score = min_score;
    if (transaction_type) params.transaction_type = transaction_type;
    if (user_id) params.user_id = user_id;

    return this.http.get<SuspiciousEventListResponse>(`${this.apiUrl}/admin/suspicious-events`, {
      headers: this.authHeaders(),
      params
    });
  }

  updateSuspiciousEvent(
    eventId: number,
    payload: SuspiciousEventUpdatePayload
  ): Observable<SuspiciousEvent> {
    return this.http.put<SuspiciousEvent>(
      `${this.apiUrl}/admin/suspicious-events/${eventId}`,
      payload,
      { headers: this.authHeaders() }
    );
  }
}

