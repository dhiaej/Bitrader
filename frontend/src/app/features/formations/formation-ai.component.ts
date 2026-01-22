import { Component, OnInit, OnDestroy, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { trigger, transition, style, animate } from '@angular/animations';
import { Subscription } from 'rxjs';
import { FormationService, Formation, Lesson, UserProgress, ChatRequest } from '../../core/services/formation.service';
import { AuthService } from '../../core/services/auth.service';
import { MarketDataService } from '../../core/services/market-data.service';
import { environment } from '../../../environments/environment';

export interface ChatMessage {
  id: number;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

@Component({
  selector: 'app-formation-ai',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './formation-ai.component.html',
  styleUrls: ['./formation-ai.component.scss'],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ]),
    trigger('slideIn', [
      transition(':enter', [
        style({ transform: 'translateX(-100%)' }),
        animate('300ms ease-out', style({ transform: 'translateX(0)' }))
      ])
    ])
  ]
})
export class FormationAIComponent implements OnInit, OnDestroy {
  // Signals
  messages = signal<ChatMessage[]>([]);
  isLoading = signal(false);
  selectedFormation = signal<Formation | null>(null);
  formations = signal<Formation[]>([]);
  userProgress = signal<UserProgress | null>(null);
  currentMessage = signal('');
  selectedLevel = signal<string>('ALL');
  
  // Computed
  filteredFormations = computed(() => {
    const level = this.selectedLevel();
    if (level === 'ALL') {
      return this.formations();
    }
    return this.formations().filter(f => f.level === level);
  });
  
  progressInfo = computed(() => {
    const progress = this.userProgress();
    const formation = this.selectedFormation();
    if (!progress || !formation) {
      return { completed: 0, total: 0, percentage: 0 };
    }
    const total = formation.content_json.length;
    const completed = progress.completed_lessons.length;
    return {
      completed,
      total,
      percentage: total > 0 ? (completed / total) * 100 : 0
    };
  });
  
  canCreateYouTubeFormation = computed(() => {
    const title = this.youtubeTitle().trim();
    const urls = this.youtubeUrls().filter(u => u.trim() !== '');
    return title.length > 0 && urls.length > 0 && !this.isCreating();
  });
  
  // User ID
  userId = signal<number | null>(null);
  isAdmin = signal(false);
  
  // Subscriptions
  private userSubscription?: Subscription;
  
  // Video Player State
  showVideoPlayer = signal(false);
  currentVideoUrl = signal<string | null>(null);
  currentVideoTitle = signal<string>('');
  currentLesson = signal<Lesson | null>(null);
  safeVideoUrl = signal<SafeResourceUrl | null>(null);
  
  // Text Lesson Modal State
  showTextLessonModal = signal(false);
  textLessonTitle = signal<string>('');
  textLessonContent = signal<string>('');
  
  // Course Generator State
  showGenerator = signal(false);
  generatorSymbol = signal<string>('');
  generatorLevel = signal<string>('INTERMEDIATE');
  availableSymbols = signal<string[]>([]);
  isGenerating = signal(false);
  generatedCourse = signal<any>(null);
  generatorError = signal<string | null>(null);
  
  // YouTube Formation Creation State
  showYouTubeForm = signal(false);
  youtubeTitle = signal<string>('');
  youtubeDescription = signal<string>('');
  youtubeLevel = signal<string>('INTERMEDIATE');
  youtubeUrls = signal<string[]>(['']);
  youtubeTitles = signal<string[]>(['']);
  isCreating = signal(false);
  createError = signal<string | null>(null);
  createSuccess = signal<string | null>(null);
  
  constructor(
    private formationService: FormationService,
    private authService: AuthService,
    private marketDataService: MarketDataService,
    private sanitizer: DomSanitizer
  ) {
    // Auto-scroll to bottom when new messages arrive
    effect(() => {
      this.messages();
      setTimeout(() => {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      }, 100);
    });
  }
  
  ngOnInit() {
    // Load initial user data
    const user = this.authService.getCurrentUser();
    if (user) {
      this.userId.set(user.id);
      this.isAdmin.set(user.is_admin || false);
    }
    
    // Subscribe to user changes to update admin status
    this.userSubscription = this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.userId.set(user.id);
        this.isAdmin.set(user.is_admin || false);
      } else {
        this.userId.set(null);
        this.isAdmin.set(false);
      }
    });
    
    this.loadFormations();
    this.loadAvailableSymbols();
  }
  
  ngOnDestroy() {
    if (this.userSubscription) {
      this.userSubscription.unsubscribe();
    }
  }
  
  loadAvailableSymbols() {
    // No longer needed - users can enter any coin name/symbol
    // Keeping for backwards compatibility but not using it
    this.marketDataService.getAllPrices().subscribe({
      next: (data: any) => {
        const symbols = Object.keys(data.prices || {});
        this.availableSymbols.set(symbols.map(s => s.replace('-USD', '')));
      },
      error: (error: any) => {
        console.error('Error loading symbols:', error);
        // Fallback to common symbols (for reference only)
        this.availableSymbols.set(['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE', 'DOT']);
      }
    });
  }
  
  toggleGenerator() {
    this.showGenerator.set(!this.showGenerator());
    if (this.showGenerator() && this.availableSymbols().length === 0) {
      this.loadAvailableSymbols();
    }
  }
  
  toggleYouTubeForm() {
    this.showYouTubeForm.set(!this.showYouTubeForm());
    if (!this.showYouTubeForm()) {
      // Reset form when closing
      this.youtubeTitle.set('');
      this.youtubeDescription.set('');
      this.youtubeLevel.set('INTERMEDIATE');
      this.youtubeUrls.set(['']);
      this.youtubeTitles.set(['']);
      this.createError.set(null);
      this.createSuccess.set(null);
    }
  }
  
  addYouTubeUrl() {
    this.youtubeUrls.update(urls => [...urls, '']);
    this.youtubeTitles.update(titles => [...titles, '']);
  }
  
  removeYouTubeUrl(index: number) {
    if (this.youtubeUrls().length > 1) {
      this.youtubeUrls.update(urls => urls.filter((_, i) => i !== index));
      this.youtubeTitles.update(titles => titles.filter((_, i) => i !== index));
    }
  }
  
  updateYouTubeUrl(index: number, value: string) {
    const urls = [...this.youtubeUrls()];
    urls[index] = value;
    this.youtubeUrls.set(urls);
  }
  
  updateYouTubeTitle(index: number, value: string) {
    const titles = [...this.youtubeTitles()];
    titles[index] = value;
    this.youtubeTitles.set(titles);
  }
  
  getYouTubeUrl(index: number): string {
    return this.youtubeUrls()[index] || '';
  }
  
  getYouTubeTitle(index: number): string {
    return this.youtubeTitles()[index] || '';
  }
  
  createYouTubeFormation() {
    const title = this.youtubeTitle().trim();
    const urls = this.youtubeUrls().filter(url => url.trim() !== '');
    
    if (!title) {
      this.createError.set('Please enter a title for the formation');
      return;
    }
    
    if (urls.length === 0) {
      this.createError.set('Please enter at least one YouTube URL');
      return;
    }
    
    // Validate YouTube URLs
    const youtubeUrlPattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
      for (const url of urls) {
        if (!youtubeUrlPattern.test(url)) {
          this.createError.set(`Invalid YouTube URL: ${url}`);
          return;
        }
      }
    
    this.isCreating.set(true);
    this.createError.set(null);
    this.createSuccess.set(null);
    
    const titles = this.youtubeTitles().filter((t, i) => i < urls.length && t.trim() !== '');
    
    this.formationService.createYouTubeFormation({
      title: title,
      description: this.youtubeDescription().trim() || undefined,
      level: this.youtubeLevel(),
      video_urls: urls,
      video_titles: titles.length > 0 ? titles : undefined
    }).subscribe({
      next: (result) => {
        this.createSuccess.set(
          `Formation created successfully! ${result.videos_count} videos added.`
        );
        this.isCreating.set(false);
        
        // Reload formations after 2 seconds
        setTimeout(() => {
          this.loadFormations();
          this.toggleYouTubeForm();
          // Reset form
          this.youtubeTitle.set('');
          this.youtubeDescription.set('');
          this.youtubeLevel.set('INTERMEDIATE');
          this.youtubeUrls.set(['']);
          this.youtubeTitles.set(['']);
          this.createSuccess.set(null);
        }, 2000);
      },
      error: (error) => {
        console.error('Error creating YouTube formation:', error);
        const errorMessage = error.error?.detail || 'Error creating the formation';
        this.createError.set(errorMessage);
        this.isCreating.set(false);
      }
    });
  }
  
  generateCourse(retryCount: number = 0) {
    const symbol = this.generatorSymbol();
    if (!symbol) {
      this.generatorError.set('Please select a symbol');
      return;
    }
    
    this.isGenerating.set(true);
    this.generatorError.set(null);
    this.generatedCourse.set(null);
    
    this.formationService.generateCourse(symbol, this.generatorLevel()).subscribe({
      next: (result) => {
        this.generatedCourse.set(result.formation);
        this.isGenerating.set(false);
      },
      error: (error: any) => {
        console.error('Error generating course:', error);
        const errorMessage = error.error?.detail || 'Error generating the course';
        
        // If it's a JSON parsing error and we haven't retried yet, retry automatically
        if (errorMessage.includes('Invalid JSON') && retryCount < 2) {
          console.log(`Retrying course generation (attempt ${retryCount + 1}/2)...`);
          setTimeout(() => {
            this.generateCourse(retryCount + 1);
          }, 1000); // Wait 1 second before retrying
          return;
        }
        
        // Improved error message
        let userFriendlyMessage = errorMessage;
        if (errorMessage.includes('Invalid JSON')) {
          userFriendlyMessage = 'JSON format error in AI response. Please try again. If the problem persists, the AI may need better formatting instructions.';
        } else if (errorMessage.includes('API key')) {
          userFriendlyMessage = 'Invalid or missing API key. Please configure OPENAI_API_KEY, GEMINI_API_KEY or GROQ_API_KEY in the backend .env file.';
        }
        
        this.generatorError.set(userFriendlyMessage);
        this.isGenerating.set(false);
      }
    });
  }
  
  saveGeneratedCourse() {
    const symbol = this.generatorSymbol();
    if (!symbol) {
      return;
    }
    
    this.isGenerating.set(true);
    this.generatorError.set(null);
    
    this.formationService.generateAndSaveCourse(symbol, this.generatorLevel()).subscribe({
      next: (formation) => {
        this.isGenerating.set(false);
        this.generatedCourse.set(null);
        this.showGenerator.set(false);
        this.generatorSymbol.set('');
        // Reload formations
        this.loadFormations();
      },
      error: (error: any) => {
        console.error('Error saving course:', error);
        this.generatorError.set(error.error?.detail || 'Error saving the course');
        this.isGenerating.set(false);
      }
    });
  }
  
  getOptionLetter(index: number): string {
    return String.fromCharCode(65 + index);
  }
  
  loadFormations() {
    this.formationService.getFormations().subscribe({
      next: (formations) => {
        this.formations.set(formations);
      },
      error: (error) => {
        console.error('Error loading formations:', error);
      }
    });
  }
  
  selectFormation(formation: Formation) {
    console.log('Selected formation:', formation);
    console.log('Formation content_json:', formation.content_json);
    this.selectedFormation.set(formation);
    this.loadUserProgress(formation.id);
  }
  
  loadUserProgress(formationId: number) {
    const userId = this.userId();
    if (!userId) return;
    
    this.formationService.getUserProgress(formationId, userId).subscribe({
      next: (progress) => {
        this.userProgress.set(progress);
      },
      error: (error) => {
        console.error('Error loading progress:', error);
        // Set default progress if not found
        this.userProgress.set({
          id: 0,
          user_id: userId,
          formation_id: formationId,
          completed_lessons: [],
          current_lesson_id: undefined,
          status: 'NOT_STARTED',
          progress_percentage: 0,
          started_at: new Date().toISOString(),
          completed_at: undefined
        });
      }
    });
  }
  
  filterByLevel(level: string) {
    this.selectedLevel.set(level);
  }
  
  sendMessage() {
    const message = this.currentMessage().trim();
    if (!message || this.isLoading()) return;
    
    const userId = this.userId();
    if (!userId) return;
    
    // Add user message to chat
    const userMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    this.messages.update(msgs => [...msgs, userMessage]);
    this.currentMessage.set('');
    this.isLoading.set(true);
    
    // Build context
    const context = this.buildContext();
    
    // Send to Gemini
    const request: ChatRequest = {
      question: message,
      userId: userId,
      context: context
    };
    
    this.formationService.askGemini(request).subscribe({
      next: (response) => {
        const aiMessage: ChatMessage = {
          id: Date.now() + 1,
          role: 'ai',
          content: response.response,
          timestamp: new Date()
        };
        this.messages.update(msgs => [...msgs, aiMessage]);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error sending message:', error);
        const errorMessage: ChatMessage = {
          id: Date.now() + 1,
          role: 'ai',
          content: '❌ Sorry, an error occurred. Please try again.',
          timestamp: new Date()
        };
        this.messages.update(msgs => [...msgs, errorMessage]);
        this.isLoading.set(false);
      }
    });
  }
  
  buildContext(): string {
    const formation = this.selectedFormation();
    const progress = this.userProgress();
    
    if (!formation) {
      return 'No formation selected.';
    }
    
    const contextParts = [
      `Current formation: ${formation.title} (${formation.level})`,
      `Description: ${formation.description || 'No description'}`
    ];
    
    if (progress) {
      const total = formation.content_json.length;
      const completed = progress.completed_lessons.length;
      contextParts.push(
        `Progress: ${completed}/${total} lessons completed (${progress.progress_percentage.toFixed(1)}%)`,
        `Status: ${progress.status}`
      );
      
      if (progress.current_lesson_id) {
        const currentLesson = formation.content_json.find(l => l.id === progress.current_lesson_id);
        if (currentLesson) {
          contextParts.push(`Current lesson: ${currentLesson.title} (${currentLesson.type})`);
        }
      }
    }
    
    return contextParts.join('\n');
  }
  
  navigateToLesson(lesson: Lesson) {
    const formation = this.selectedFormation();
    if (!formation) return;
    
    console.log('Navigating to lesson:', lesson);
    
    // Check if previous lessons are completed (enforce sequential completion)
    const progress = this.userProgress();
    const completedLessons = progress?.completed_lessons || [];
    const currentIndex = formation.content_json.findIndex(l => l.id === lesson.id);
    
    // Check if all previous lessons are completed
    if (currentIndex > 0) {
      const previousLessons = formation.content_json.slice(0, currentIndex);
      const allPreviousCompleted = previousLessons.every(l => completedLessons.includes(l.id));
      
      if (!allPreviousCompleted) {
        const firstIncomplete = previousLessons.find(l => !completedLessons.includes(l.id));
        if (firstIncomplete) {
          this.textLessonTitle.set('Lesson Locked');
          this.textLessonContent.set(`Please complete "${firstIncomplete.title}" before continuing.`);
          this.showTextLessonModal.set(true);
          return;
        }
      }
    }
    
    // Handle video display
    if (lesson.type === 'VIDEO') {
      // Get video URL from lesson data
      let videoUrl = lesson.data;
      
      console.log('Video URL from lesson.data:', videoUrl);
      
      if (!videoUrl) {
        console.error('No video URL found in lesson data', lesson);
        this.textLessonTitle.set('Video Not Found');
        this.textLessonContent.set('No video URL found for this lesson.');
        this.showTextLessonModal.set(true);
        return;
      }
      
      // Determine the YouTube embed URL
      let embedUrl = '';
      
      // Check if it's already a YouTube embed URL
      if (videoUrl.includes('youtube.com/embed/')) {
        embedUrl = videoUrl;
      } 
      // Check if it's a regular YouTube URL that needs conversion
      else if (videoUrl.includes('youtu.be/') || videoUrl.includes('youtube.com/watch')) {
        // Extract YouTube video ID
        let youtubeId = '';
        if (videoUrl.includes('youtu.be/')) {
          youtubeId = videoUrl.split('youtu.be/')[1].split('?')[0].split('&')[0];
        } else if (videoUrl.includes('youtube.com/watch')) {
          const match = videoUrl.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
          youtubeId = match ? match[1] : '';
        }
        
        console.log('Extracted YouTube ID:', youtubeId);
        
        if (youtubeId) {
          embedUrl = `https://www.youtube.com/embed/${youtubeId}`;
        } else {
          console.error('Could not extract YouTube video ID from URL:', videoUrl);
          this.textLessonTitle.set('Invalid YouTube URL');
          this.textLessonContent.set('Invalid YouTube URL format. Please check the URL format.');
          this.showTextLessonModal.set(true);
          return;
        }
      }
      
      if (embedUrl) {
        // Add autoplay parameter
        const urlWithParams = embedUrl + (embedUrl.includes('?') ? '&' : '?') + 'autoplay=1&rel=0';
        console.log('Setting YouTube embed URL:', urlWithParams);
        
        // Sanitize the URL for Angular
        const safeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(urlWithParams);
        this.safeVideoUrl.set(safeUrl);
        this.currentVideoUrl.set(embedUrl);
        this.currentVideoTitle.set(lesson.title);
        this.currentLesson.set(lesson);
        this.showVideoPlayer.set(true);
        return;
      }
      
      // Fallback for other video types (direct video URLs)
      if (videoUrl.startsWith('http://') || videoUrl.startsWith('https://') || videoUrl.startsWith('/')) {
        this.currentVideoUrl.set(this.getFullVideoUrl(videoUrl));
        this.currentVideoTitle.set(lesson.title);
        this.currentLesson.set(lesson);
        this.showVideoPlayer.set(true);
      } else {
        console.error('Invalid video URL format:', videoUrl);
        this.textLessonTitle.set('Invalid URL Format');
        this.textLessonContent.set(`Invalid URL format: ${videoUrl}`);
        this.showTextLessonModal.set(true);
      }
    } else {
      // For non-video lessons, show content
      this.showVideoContent(lesson);
    }
  }
  
  getFullVideoUrl(url: string): string {
    // If it's already a full URL, return as is
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    // If it's a relative URL, prepend the API base URL
    if (url.startsWith('/')) {
      const baseUrl = environment.apiUrl.replace('/api', '');
      return `${baseUrl}${url}`;
    }
    return url;
  }
  
  showVideoContent(lesson: Lesson) {
    this.textLessonTitle.set(lesson.title);
    this.textLessonContent.set(lesson.data);
    this.showTextLessonModal.set(true);
  }
  
  closeTextLessonModal() {
    this.showTextLessonModal.set(false);
    this.textLessonTitle.set('');
    this.textLessonContent.set('');
  }
  
  canAccessLesson(lesson: Lesson): boolean {
    const formation = this.selectedFormation();
    if (!formation) return false;
    
    const progress = this.userProgress();
    const completedLessons = progress?.completed_lessons || [];
    const currentIndex = formation.content_json.findIndex(l => l.id === lesson.id);
    
    // First lesson is always accessible
    if (currentIndex === 0) return true;
    
    // Check if all previous lessons are completed
    const previousLessons = formation.content_json.slice(0, currentIndex);
    return previousLessons.every(l => completedLessons.includes(l.id));
  }
  
  closeVideoPlayer() {
    this.showVideoPlayer.set(false);
    this.currentVideoUrl.set(null);
    this.currentVideoTitle.set('');
    this.currentLesson.set(null);
    this.safeVideoUrl.set(null);
  }
  
  onVideoLoaded(videoElement: HTMLVideoElement) {
    if (videoElement) {
      videoElement.play().catch(error => {
        console.log('Auto-play prevented:', error);
        // Auto-play was prevented, user will need to click play manually
      });
    }
  }
  
  getCurrentVideoUrl(): string | null {
    const url = this.currentVideoUrl();
    console.log('Current video URL:', url);
    return url;
  }
  
  completeLesson(lesson: Lesson) {
    const formation = this.selectedFormation();
    const userId = this.userId();
    if (!formation || !userId) return;
    
    this.formationService.completeLesson(formation.id, userId, lesson.id).subscribe({
      next: (progress) => {
        this.userProgress.set(progress);
        
        // Check if formation is completed
        if (progress.status === 'COMPLETED') {
          // Optionally generate certificate
          this.formationService.generateCertificate(formation.id, userId).subscribe({
            next: (cert) => {
              console.log('Certificate generated:', cert.certificate_url);
            },
            error: (error) => {
              console.error('Error generating certificate:', error);
            }
          });
        }
      },
      error: (error) => {
        console.error('Error completing lesson:', error);
      }
    });
  }
  
  isLessonCompleted(lessonId: string): boolean {
    const progress = this.userProgress();
    if (!progress) return false;
    return progress.completed_lessons.includes(lessonId);
  }
  
  getLevelBadgeClass(level: string): string {
    switch (level) {
      case 'BEGINNER':
        return 'bg-green-600';
      case 'INTERMEDIATE':
        return 'bg-yellow-600';
      case 'ADVANCED':
        return 'bg-red-600';
      default:
        return 'bg-gray-600';
    }
  }
  
  getLessonTypeIcon(type: string): string {
    switch (type) {
      case 'TEXT':
        return '📄';
      case 'VIDEO':
        return '🎥';
      case 'QUIZ':
        return '❓';
      case 'CHALLENGE':
        return '🎯';
      default:
        return '📝';
    }
  }
}

