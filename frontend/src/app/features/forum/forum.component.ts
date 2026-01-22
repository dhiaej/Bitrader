import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ForumService, ForumCategory } from '../../core/services/forum.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-forum',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './forum.component.html',
  styleUrls: ['./forum.component.scss']
})
export class ForumComponent implements OnInit {
  categories: ForumCategory[] = [];
  groupedCategories: { level: string; categories: ForumCategory[] }[] = [];
  loading = true;
  error: string | null = null;

  constructor(
    private forumService: ForumService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadCategories();
  }

  loadCategories(): void {
    this.loading = true;
    this.error = null;

    this.forumService.getCategories().subscribe({
      next: (categories) => {
        this.categories = categories;
        this.groupCategories();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load forum categories';
        console.error('Error loading categories:', err);
        this.loading = false;
      }
    });
  }

  groupCategories(): void {
    const groups: { [key: number]: ForumCategory[] } = {};
    
    this.categories.forEach(cat => {
      const level = cat.min_reputation_required;
      if (!groups[level]) {
        groups[level] = [];
      }
      groups[level].push(cat);
    });

    this.groupedCategories = Object.keys(groups)
      .map(level => parseInt(level))
      .sort((a, b) => a - b)
      .map(level => ({
        level: this.getLevelName(level),
        categories: groups[level]
      }));
  }

  getLevelName(reputation: number): string {
    if (reputation >= 1000) return 'Expert';
    if (reputation >= 500) return 'Pro';
    return 'Normal';
  }

  getLevelBadgeClass(reputation: number): string {
    if (reputation >= 1000) return 'badge-expert';
    if (reputation >= 500) return 'badge-pro';
    return 'badge-normal';
  }

  canAccessCategory(category: ForumCategory): boolean {
    const user = this.authService.getCurrentUser();
    if (!user) return false;
    return true;
  }

  get currentUser() {
    return this.authService.getCurrentUser();
  }

  getUserReputationScore(): number {
    const user = this.currentUser;
    return (user && 'reputation_score' in user && user.reputation_score) ? user.reputation_score : 0;
  }
}

