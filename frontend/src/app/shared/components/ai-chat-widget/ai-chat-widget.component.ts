import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AiAssistantService, ChatMessage } from '../../../core/services/ai-assistant.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-ai-chat-widget',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ai-chat-widget.component.html',
  styleUrls: ['./ai-chat-widget.component.scss']
})
export class AiChatWidgetComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('chatMessages') private chatMessagesContainer!: ElementRef;

  isOpen = false;
  isLoading = false;
  messages: ChatMessage[] = [];
  userInput = '';
  private subscriptions: Subscription[] = [];
  private shouldScrollToBottom = false;

  quickSuggestions = [
    { label: 'Market Analysis', type: 'market_analysis' as const, icon: '📊' },
    { label: 'Trading Tip', type: 'trading_tip' as const, icon: '💡' },
    { label: 'Risk Assessment', type: 'risk_assessment' as const, icon: '⚠️' }
  ];

  constructor(private aiService: AiAssistantService) {}

  ngOnInit() {
    this.loadChatHistory();
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  toggleChat() {
    this.isOpen = !this.isOpen;
    if (this.isOpen && this.messages.length === 0) {
      this.loadChatHistory();
    }
  }

  loadChatHistory() {
    const sub = this.aiService.getChatHistory().subscribe({
      next: (history) => {
        this.messages = history;
        this.shouldScrollToBottom = true;
      },
      error: (error) => {
        console.error('Failed to load chat history:', error);
      }
    });
    this.subscriptions.push(sub);
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: this.userInput,
      timestamp: new Date().toISOString()
    };

    this.messages.push(userMessage);
    this.shouldScrollToBottom = true;
    const messageContent = this.userInput;
    this.userInput = '';
    this.isLoading = true;

    const sub = this.aiService.sendMessage(messageContent).subscribe({
      next: (response) => {
        this.messages.push(response.message);
        this.isLoading = false;
        this.shouldScrollToBottom = true;
      },
      error: (error) => {
        console.error('Failed to send message:', error);
        this.messages.push({
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString()
        });
        this.isLoading = false;
        this.shouldScrollToBottom = true;
      }
    });
    this.subscriptions.push(sub);
  }

  useQuickSuggestion(type: 'market_analysis' | 'trading_tip' | 'risk_assessment') {
    this.isLoading = true;
    const sub = this.aiService.getQuickSuggestion(type).subscribe({
      next: (response) => {
        this.messages.push({
          role: 'assistant',
          content: response.suggestion,
          timestamp: new Date().toISOString()
        });
        this.isLoading = false;
        this.shouldScrollToBottom = true;
      },
      error: (error) => {
        console.error('Failed to get suggestion:', error);
        this.isLoading = false;
      }
    });
    this.subscriptions.push(sub);
  }

  clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
      const sub = this.aiService.clearHistory().subscribe({
        next: () => {
          this.messages = [];
        },
        error: (error) => {
          console.error('Failed to clear chat:', error);
        }
      });
      this.subscriptions.push(sub);
    }
  }

  private scrollToBottom() {
    try {
      if (this.chatMessagesContainer) {
        const element = this.chatMessagesContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    } catch (err) {
      console.error('Scroll error:', err);
    }
  }

  formatTime(timestamp?: string): string {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  }

  onKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}
