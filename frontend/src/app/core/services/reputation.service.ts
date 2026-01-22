import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Review {
  id: number;
  trade_id: number;
  reviewer_id: number;
  reviewed_user_id: number;
  rating: number;
  comment?: string | null;
  created_at: string;
}

export interface ReputationStats {
  id: number;
  user_id: number;
  score: number;
  total_trades: number;
  completed_trades: number;
  disputed_trades: number;
  completion_rate: number;
  average_response_time: number;
  average_rating: number;
  review_count: number;
  badges: string[];
}

export interface ReputationProfile {
  user: {
    id: number;
    username: string;
    full_name?: string | null;
    avatar_url?: string | null;
  };
  reputation: ReputationStats;
  recent_reviews: Review[];
}

export interface ReviewedTradesPayload {
  trade_ids: number[];
}

export interface ReviewRequest {
  trade_id: number;
  rating: number;
  comment?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ReputationService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getMyProfile(): Observable<ReputationProfile> {
    return this.http.get<ReputationProfile>(`${this.apiUrl}/reputation/me`);
  }

  getProfile(username: string): Observable<ReputationProfile> {
    return this.http.get<ReputationProfile>(`${this.apiUrl}/reputation/user/${username}`);
  }

  getUserReviews(username: string, limit = 20): Observable<Review[]> {
    return this.http.get<Review[]>(`${this.apiUrl}/reputation/user/${username}/reviews?limit=${limit}`);
  }

  submitReview(payload: ReviewRequest): Observable<Review> {
    return this.http.post<Review>(`${this.apiUrl}/reputation/reviews`, payload);
  }

  getReviewedTradeIds(): Observable<Set<number>> {
    return this.http.get<ReviewedTradesPayload>(`${this.apiUrl}/reputation/reviews/my/trades`).pipe(
      map((response) => new Set(response.trade_ids))
    );
  }
}

