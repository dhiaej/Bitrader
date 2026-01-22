import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ChatMessage {
  id?: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatResponse {
  message: ChatMessage;
  suggestion?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AiAssistantService {
  private apiUrl = `${environment.apiUrl}/ai`;

  constructor(private http: HttpClient) {}

  /**
   * Send a message to the AI assistant
   */
  sendMessage(content: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, { content });
  }

  /**
   * Get chat history
   */
  getChatHistory(limit: number = 50): Observable<ChatMessage[]> {
    return this.http.get<ChatMessage[]>(`${this.apiUrl}/chat/history?limit=${limit}`);
  }

  /**
   * Clear chat history
   */
  clearHistory(): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}/chat/history`);
  }

  /**
   * Get quick suggestions
   */
  getQuickSuggestion(type: 'market_analysis' | 'trading_tip' | 'risk_assessment'): Observable<{ suggestion: string }> {
    return this.http.get<{ suggestion: string }>(`${this.apiUrl}/suggestions/${type}`);
  }
}
