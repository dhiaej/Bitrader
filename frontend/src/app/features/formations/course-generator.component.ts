import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { trigger, transition, style, animate } from '@angular/animations';
import { FormationService } from '../../core/services/formation.service';
import { MarketDataService } from '../../core/services/market-data.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-course-generator',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './course-generator.component.html',
  styleUrls: ['./course-generator.component.scss'],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('200ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class CourseGeneratorComponent implements OnInit {
  // Available symbols
  availableSymbols = signal<string[]>([]);
  selectedSymbol = signal<string>('');
  selectedLevel = signal<string>('INTERMEDIATE');
  
  // Generation state
  isGenerating = signal(false);
  generatedCourse = signal<any>(null);
  error = signal<string | null>(null);
  
  // Current user
  isAdmin = signal(false);
  
  constructor(
    private formationService: FormationService,
    private marketDataService: MarketDataService,
    private authService: AuthService,
    private router: Router
  ) {}
  
  ngOnInit() {
    const user = this.authService.getCurrentUser();
    if (user) {
      this.isAdmin.set(user.is_admin || false);
    }
    
    this.loadAvailableSymbols();
  }
  
  loadAvailableSymbols() {
    this.marketDataService.getAllPrices().subscribe({
      next: (data: any) => {
        const symbols = Object.keys(data.prices || {});
        this.availableSymbols.set(symbols.map(s => s.replace('-USD', '')));
      },
      error: (error: any) => {
        console.error('Error loading symbols:', error);
        // Fallback to common symbols
        this.availableSymbols.set(['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE', 'DOT']);
      }
    });
  }
  
  generateCourse() {
    const symbol = this.selectedSymbol();
    if (!symbol) {
      this.error.set('Veuillez sélectionner un symbole');
      return;
    }
    
    this.isGenerating.set(true);
    this.error.set(null);
    this.generatedCourse.set(null);
    
    this.formationService.generateCourse(symbol, this.selectedLevel()).subscribe({
      next: (result) => {
        this.generatedCourse.set(result.formation);
        this.isGenerating.set(false);
      },
      error: (error) => {
        console.error('Error generating course:', error);
        this.error.set(error.error?.detail || 'Erreur lors de la génération du cours');
        this.isGenerating.set(false);
      }
    });
  }
  
  saveCourse() {
    const symbol = this.selectedSymbol();
    if (!symbol) {
      return;
    }
    
    this.isGenerating.set(true);
    this.error.set(null);
    
    this.formationService.generateAndSaveCourse(symbol, this.selectedLevel()).subscribe({
      next: (formation) => {
        this.isGenerating.set(false);
        // Navigate to formations page
        this.router.navigate(['/formations']);
      },
      error: (error) => {
        console.error('Error saving course:', error);
        this.error.set(error.error?.detail || 'Erreur lors de la sauvegarde du cours');
        this.isGenerating.set(false);
      }
    });
  }
  
  getLevelLabel(level: string): string {
    const labels: { [key: string]: string } = {
      'BEGINNER': 'Débutant',
      'INTERMEDIATE': 'Intermédiaire',
      'ADVANCED': 'Avancé'
    };
    return labels[level] || level;
  }
  
  getLessonIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'TEXT': '📄',
      'VIDEO': '🎥',
      'QUIZ': '❓',
      'CHALLENGE': '🎯'
    };
    return icons[type] || '📝';
  }
  
  getOptionLetter(index: number): string {
    return String.fromCharCode(65 + index);
  }
}

