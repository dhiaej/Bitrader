import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User } from './auth.service';

export interface UpdateProfilePayload {
  full_name?: string | null;
  email?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl = environment.apiUrl;
  private apiBaseUrl = this.apiUrl.replace(/\/api$/, '');

  constructor(private http: HttpClient) {}

  private authHeaders(isJson = true): HttpHeaders {
    const token = localStorage.getItem('access_token');
    let headers = new HttpHeaders({
      Authorization: token ? `Bearer ${token}` : ''
    });
    if (isJson) {
      headers = headers.set('Content-Type', 'application/json');
    }
    return headers;
  }

  getProfile(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/profile`, {
      headers: this.authHeaders()
    });
  }

  updateProfile(payload: UpdateProfilePayload): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/users/profile`, payload, {
      headers: this.authHeaders()
    });
  }

  uploadAvatar(file: File): Observable<User> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<User>(`${this.apiUrl}/users/profile/avatar`, formData, {
      headers: this.authHeaders(false)
    });
  }

  resolveAvatarUrl(path?: string | null): string {
    if (!path) {
      return '';
    }
    if (path.startsWith('http')) {
      return path;
    }
    return `${this.apiBaseUrl}${path}`;
  }
}

