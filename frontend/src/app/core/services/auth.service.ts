import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  avatar_url?: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  reputation_score?: number;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
}

export interface FaceRegisterResponse {
  message: string;
  success: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Load user on service initialization if token exists
    if (this.hasToken()) {
      this.loadCurrentUser();
    }
  }

  private hasToken(): boolean {
    return !!localStorage.getItem('access_token');
  }

  register(data: RegisterData): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/auth/register`, data);
  }

  login(username: string, password: string): Observable<LoginResponse> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, formData)
      .pipe(
        tap(response => {
          localStorage.setItem('access_token', response.access_token);
          localStorage.setItem('user_id', response.user_id.toString());
          localStorage.setItem('username', response.username);
          this.isAuthenticatedSubject.next(true);
          this.loadCurrentUser();
        })
      );
  }

  faceLogin(username: string, image: Blob): Observable<LoginResponse> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('file', image, 'face-login.jpg');

    return this.http.post<LoginResponse>(`${this.apiUrl}/auth/face-login`, formData)
      .pipe(
        tap(response => {
          localStorage.setItem('access_token', response.access_token);
          localStorage.setItem('user_id', response.user_id.toString());
          localStorage.setItem('username', response.username);
          this.isAuthenticatedSubject.next(true);
          this.loadCurrentUser();
        })
      );
  }

  registerFace(image: Blob): Observable<FaceRegisterResponse> {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return throwError(() => new Error('User not authenticated'));
    }

    const formData = new FormData();
    formData.append('file', image, 'face-register.jpg');

    return this.http.post<FaceRegisterResponse>(`${this.apiUrl}/auth/face-register`, formData, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
    this.router.navigate(['/login']);
  }

  loadCurrentUser(): void {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    this.http.get<User>(`${this.apiUrl}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }).subscribe({
      next: (user) => this.currentUserSubject.next(user),
      error: () => this.logout()
    });
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }
}
