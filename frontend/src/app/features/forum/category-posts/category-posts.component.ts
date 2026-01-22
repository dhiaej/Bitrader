import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { ForumService, ForumCategory, ForumPost, ForumPostList } from '../../../core/services/forum.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-category-posts',
  standalone: true,
  imports: [CommonModule, RouterModule, ReactiveFormsModule],
  templateUrl: './category-posts.component.html',
  styleUrls: ['./category-posts.component.scss']
})
export class CategoryPostsComponent implements OnInit {
  categoryId!: number;
  category: ForumCategory | null = null;
  posts: ForumPost[] = [];
  loading = true;
  error: string | null = null;
  
  // Pagination
  currentPage = 1;
  pageSize = 20;
  totalPosts = 0;
  totalPages = 1;
  
  // Sorting
  sortForm: FormGroup;
  sortBy: 'activity' | 'newest' | 'votes' | 'oldest' = 'activity';
  
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private forumService: ForumService,
    private authService: AuthService,
    private fb: FormBuilder
  ) {
    this.sortForm = this.fb.group({
      sort: ['activity']
    });
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      this.categoryId = +params['id'];
      this.loadCategory();
      this.loadPosts();
    });
    
    this.sortForm.get('sort')?.valueChanges.subscribe(sort => {
      this.sortBy = sort;
      this.currentPage = 1;
      this.loadPosts();
    });
  }

  loadCategory(): void {
    this.forumService.getCategory(this.categoryId).subscribe({
      next: (category) => {
        this.category = category;
      },
      error: (err) => {
        console.error('Error loading category:', err);
      }
    });
  }

  loadPosts(): void {
    this.loading = true;
    this.error = null;

    this.forumService.getPosts(this.categoryId, this.currentPage, this.pageSize, this.sortBy).subscribe({
      next: (data: ForumPostList) => {
        this.posts = data.posts;
        this.totalPosts = data.total;
        this.totalPages = data.total_pages;
        this.currentPage = data.page;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load posts';
        console.error('Error loading posts:', err);
        this.loading = false;
      }
    });
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadPosts();
    }
  }

  canCreatePost(): boolean {
    if (!this.category || !this.authService.getCurrentUser()) return false;
    const user = this.authService.getCurrentUser()!;
    const userReputation = this.getUserReputationScore(user);
    return userReputation >= this.category.min_reputation_required;
  }

  getUserReputationScore(user?: any): number {
    if (!user) {
      const currentUser = this.authService.getCurrentUser();
      if (!currentUser) return 0;
      user = currentUser;
    }
    return (user && 'reputation_score' in user && user.reputation_score) ? user.reputation_score : 0;
  }

  get currentUser() {
    return this.authService.getCurrentUser();
  }
}

