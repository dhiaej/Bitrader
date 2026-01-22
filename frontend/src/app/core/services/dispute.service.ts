import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface DisputeCreate {
  trade_id: number;
  reason: string;
  evidence?: string;
}

export interface DisputeAddEvidence {
  evidence: string;
}

export interface DisputeResolve {
  resolution: string;
  refund_to_buyer?: boolean;
  release_to_seller?: boolean;
}

export interface DisputeResponse {
  id: number;
  trade_id: number;
  filed_by: number;
  filed_by_username?: string;
  reason: string;
  evidence?: string;
  status: string;
  resolution?: string;
  resolved_by?: number;
  resolved_by_username?: string;
  created_at: string;
  resolved_at?: string;

  // Trade details
  trade_amount?: number;
  trade_currency?: string;
  buyer_id?: number;
  buyer_username?: string;
  seller_id?: number;
  seller_username?: string;
}

export interface DisputeListResponse {
  total: number;
  disputes: DisputeResponse[];
}

export interface DisputeDetails {
  dispute: {
    id: number;
    trade_id: number;
    filed_by: number;
    filed_by_username?: string;
    filed_by_email?: string;
    reason: string;
    evidence?: string;
    status: string;
    resolution?: string;
    resolved_by?: number;
    resolved_by_username?: string;
    created_at: string;
    resolved_at?: string;
  };
  trade: {
    id: number;
    amount: number;
    currency: string;
    fiat_currency: string;
    price: number;
    total_fiat: number;
    status: string;
    payment_method: string;
    payment_confirmed: boolean;
    created_at: string;
  };
  buyer?: {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
  };
  seller?: {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
  };
  escrow?: {
    amount: number;
    currency: string;
    status: string;
    locked_at: string;
    released_at?: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class DisputeService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    });
  }

  /**
   * File a new dispute on a P2P trade
   */
  createDispute(disputeData: DisputeCreate): Observable<DisputeResponse> {
    return this.http.post<DisputeResponse>(
      `${this.apiUrl}/disputes/`,
      disputeData,
      { headers: this.authHeaders() }
    );
  }

  /**
   * Get all disputes for the current user
   */
  getMyDisputes(): Observable<DisputeListResponse> {
    return this.http.get<DisputeListResponse>(
      `${this.apiUrl}/disputes/my-disputes`,
      { headers: this.authHeaders() }
    );
  }

  /**
   * Get details of a specific dispute
   */
  getDispute(disputeId: number): Observable<DisputeResponse> {
    return this.http.get<DisputeResponse>(
      `${this.apiUrl}/disputes/${disputeId}`,
      { headers: this.authHeaders() }
    );
  }

  /**
   * Get detailed dispute information (admin view)
   */
  getDisputeDetails(disputeId: number): Observable<DisputeDetails> {
    return this.http.get<DisputeDetails>(
      `${this.apiUrl}/admin/disputes/${disputeId}`,
      { headers: this.authHeaders() }
    );
  }

  /**
   * Add evidence to an existing dispute
   */
  addEvidence(disputeId: number, evidence: DisputeAddEvidence): Observable<DisputeResponse> {
    return this.http.post<DisputeResponse>(
      `${this.apiUrl}/disputes/${disputeId}/evidence`,
      evidence,
      { headers: this.authHeaders() }
    );
  }

  /**
   * Resolve a dispute (admin only)
   */
  resolveDispute(disputeId: number, resolutionData: DisputeResolve): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/admin/disputes/${disputeId}/resolve`,
      resolutionData,
      { headers: this.authHeaders() }
    );
  }

  /**
   * Cancel a dispute (only by filer, only if OPEN)
   */
  cancelDispute(disputeId: number): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/disputes/${disputeId}`,
      { headers: this.authHeaders() }
    );
  }

  /**
   * Get status badge color
   */
  getStatusColor(status: string): string {
    switch (status.toUpperCase()) {
      case 'OPEN':
        return '#F0B90B'; // Yellow
      case 'IN_REVIEW':
      case 'UNDER_REVIEW':
        return '#2196F3'; // Blue
      case 'RESOLVED':
        return '#0ECB81'; // Green
      case 'REJECTED':
        return '#F6465D'; // Red
      default:
        return '#848E9C'; // Gray
    }
  }

  /**
   * Get status display text
   */
  getStatusText(status: string): string {
    switch (status.toUpperCase()) {
      case 'OPEN':
        return 'Open';
      case 'IN_REVIEW':
        return 'In Review';
      case 'UNDER_REVIEW':
        return 'Under Review';
      case 'RESOLVED':
        return 'Resolved';
      case 'REJECTED':
        return 'Rejected';
      default:
        return status;
    }
  }
}
