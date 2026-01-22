import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class WebsocketService {
  private socket: Socket | null = null;
  private messageSubject = new Subject<any>();
  public messages$ = this.messageSubject.asObservable();

  private connectedSubject = new Subject<boolean>();
  public connected$ = this.connectedSubject.asObservable();

  constructor() {}

  connect(clientId: string): void {
    if (this.socket?.connected) {
      return;
    }

    // For FastAPI WebSocket endpoint
    const wsUrl = environment.wsUrl || environment.apiUrl.replace('http', 'ws');
    const fullUrl = `${wsUrl}/ws/${clientId}`;

    // Note: This is a WebSocket connection, not socket.io
    // For now, we'll use native WebSocket
    this.connectWebSocket(fullUrl);
  }

  private connectWebSocket(url: string): void {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket connected');
      this.connectedSubject.next(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.messageSubject.next(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connectedSubject.next(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.connectedSubject.next(false);
    };
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connectedSubject.next(false);
    }
  }

  send(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  on(event: string): Observable<any> {
    return new Observable(observer => {
      if (this.socket) {
        this.socket.on(event, (data: any) => {
          observer.next(data);
        });
      }
    });
  }
}
