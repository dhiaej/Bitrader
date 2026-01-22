import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Lesson {
  id: string;
  title: string;
  type: 'TEXT' | 'VIDEO' | 'QUIZ' | 'CHALLENGE';
  data: string;
  duration?: number;
}

export interface Formation {
  id: number;
  title: string;
  description?: string;
  level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  content_json: Lesson[];
  thumbnail_url?: string;
  estimated_duration?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserProgress {
  id: number;
  user_id: number;
  formation_id: number;
  completed_lessons: string[];
  current_lesson_id?: string;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  progress_percentage: number;
  started_at: string;
  completed_at?: string;
}

export interface ChatRequest {
  question: string;
  userId: number;
  context?: string;
}

export interface ChatResponse {
  response: string;
}

@Injectable({
  providedIn: 'root'
})
export class FormationService {
  private apiUrl = `${environment.apiUrl}/formations`;

  constructor(private http: HttpClient) {}

  /**
   * Get all formations with optional level filter
   */
  getFormations(level?: string): Observable<Formation[]> {
    let params = new HttpParams();
    if (level) {
      params = params.set('level', level);
    }
    return this.http.get<Formation[]>(this.apiUrl, { params });
  }

  /**
   * Get a specific formation by ID
   */
  getFormation(id: number): Observable<Formation> {
    return this.http.get<Formation>(`${this.apiUrl}/${id}`);
  }

  /**
   * Create a new formation (Admin only)
   */
  createFormation(formation: Partial<Formation>): Observable<Formation> {
    return this.http.post<Formation>(this.apiUrl, formation);
  }

  /**
   * Update a formation (Admin only)
   */
  updateFormation(id: number, formation: Partial<Formation>): Observable<Formation> {
    return this.http.put<Formation>(`${this.apiUrl}/${id}`, formation);
  }

  /**
   * Delete a formation (Admin only)
   */
  deleteFormation(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  /**
   * Get user progress for a formation
   */
  getUserProgress(formationId: number, userId: number): Observable<UserProgress> {
    return this.http.get<UserProgress>(`${this.apiUrl}/${formationId}/progress/${userId}`);
  }

  /**
   * Mark a lesson as completed
   */
  completeLesson(formationId: number, userId: number, lessonId: string): Observable<UserProgress> {
    return this.http.post<UserProgress>(
      `${this.apiUrl}/${formationId}/progress/${userId}/complete-lesson`,
      { lesson_id: lessonId }
    );
  }

  /**
   * Generate certificate for completed formation
   */
  generateCertificate(formationId: number, userId: number): Observable<{ certificate_url: string }> {
    return this.http.post<{ certificate_url: string }>(
      `${this.apiUrl}/${formationId}/certificate/${userId}`,
      {}
    );
  }

  /**
   * Ask Gemini AI a question
   */
  askGemini(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/gemini/ask`, request);
  }

  /**
   * Generate a course from market data
   */
  generateCourse(symbol: string, level?: string): Observable<{ formation: any; preview: boolean; message: string }> {
    const params: any = {};
    if (level) {
      params.level = level;
    }
    return this.http.post<{ formation: any; preview: boolean; message: string }>(
      `${this.apiUrl}/generate-course/${symbol}`,
      {},
      { params }
    );
  }

  /**
   * Generate and save a course
   */
  generateAndSaveCourse(symbol: string, level?: string): Observable<Formation> {
    const params: any = {};
    if (level) {
      params.level = level;
    }
    return this.http.post<Formation>(
      `${this.apiUrl}/generate-course/${symbol}/save`,
      {},
      { params }
    );
  }

  /**
   * Create formation with YouTube videos
   */
  createYouTubeFormation(data: {
    title: string;
    description?: string;
    level?: string;
    video_urls: string[];
    video_titles?: string[];
    user_ids?: number[];
  }): Observable<{
    formation: Formation;
    videos_count: number;
    message: string;
  }> {
    return this.http.post<{
      formation: Formation;
      videos_count: number;
      message: string;
    }>(`${this.apiUrl}/create-youtube-formation`, data);
  }

  /**
   * Assign formation to users
   */
  assignFormationToUsers(formationId: number, userIds: number[]): Observable<{ message: string; assigned_count: number; formation_id: number }> {
    return this.http.post<{ message: string; assigned_count: number; formation_id: number }>(
      `${this.apiUrl}/${formationId}/assign`,
      { user_ids: userIds }
    );
  }

  /**
   * Unassign formation from user
   */
  unassignFormationFromUser(formationId: number, userId: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}/${formationId}/assign/${userId}`);
  }

  /**
   * Get assigned users for a formation
   */
  getAssignedUsers(formationId: number): Observable<{ formation_id: number; formation_title: string; users: Array<{ id: number; username: string; email: string; full_name?: string; assigned_at: string }>; count: number }> {
    return this.http.get<{ formation_id: number; formation_title: string; users: Array<{ id: number; username: string; email: string; full_name?: string; assigned_at: string }>; count: number }>(
      `${this.apiUrl}/${formationId}/assigned-users`
    );
  }

  /**
   * Get module details including video URL
   */
  getModuleDetails(formationId: number, moduleId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${formationId}/modules/${moduleId}`);
  }
}

