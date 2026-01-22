import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ForumCategory {
  id: number;
  name: string;
  description: string | null;
  icon: string | null;
  min_reputation_required: number;
  read_only_for_lower_levels: boolean;
  parent_category_id: number | null;
  sort_order: number;
  is_active: boolean;
  post_count?: number;
  created_at: string;
}

export interface AuthorInfo {
  id: number;
  username: string;
  avatar_url: string | null;
  reputation_score: number | null;
  reputation_level: string | null;
}

export interface ForumPost {
  id: number;
  title: string;
  content: string;
  author: AuthorInfo;
  category_id: number;
  category_name: string | null;
  tags: string[] | null;
  upvotes: number;
  downvotes: number;
  view_count: number;
  comment_count: number;
  is_pinned: boolean;
  is_locked: boolean;
  user_vote: string | null;
  last_activity_at: string;
  created_at: string;
  updated_at: string | null;
}

export interface ForumComment {
  id: number;
  post_id: number;
  author: AuthorInfo;
  content: string;
  parent_comment_id: number | null;
  upvotes: number;
  downvotes: number;
  is_solution: boolean;
  user_vote: string | null;
  reply_count: number;
  replies: ForumComment[];
  created_at: string;
  updated_at: string | null;
}

export interface ForumPostDetail extends ForumPost {
  comments: ForumComment[];
}

export interface ForumPostList {
  posts: ForumPost[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ForumPostCreate {
  title: string;
  content: string;
  category_id: number;
  tags?: string[];
}

export interface ForumCommentCreate {
  content: string;
  parent_comment_id?: number;
}

export interface ForumVoteCreate {
  vote_type: 'UP' | 'DOWN';
}

@Injectable({
  providedIn: 'root'
})
export class ForumService {
  private apiUrl = `${environment.apiUrl}/forum`;

  constructor(private http: HttpClient) {}

  // Categories
  getCategories(): Observable<ForumCategory[]> {
    return this.http.get<ForumCategory[]>(`${this.apiUrl}/categories`);
  }

  getCategory(categoryId: number): Observable<ForumCategory> {
    return this.http.get<ForumCategory>(`${this.apiUrl}/categories/${categoryId}`);
  }

  // Posts
  getPosts(
    categoryId: number,
    page: number = 1,
    pageSize: number = 20,
    sort: 'activity' | 'newest' | 'votes' | 'oldest' = 'activity'
  ): Observable<ForumPostList> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString())
      .set('sort', sort);

    return this.http.get<ForumPostList>(`${this.apiUrl}/categories/${categoryId}/posts`, { params });
  }

  getPost(postId: number): Observable<ForumPostDetail> {
    return this.http.get<ForumPostDetail>(`${this.apiUrl}/posts/${postId}`);
  }

  createPost(post: ForumPostCreate): Observable<ForumPost> {
    return this.http.post<ForumPost>(`${this.apiUrl}/posts`, post);
  }

  updatePost(postId: number, post: Partial<ForumPostCreate>): Observable<ForumPost> {
    return this.http.put<ForumPost>(`${this.apiUrl}/posts/${postId}`, post);
  }

  deletePost(postId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/posts/${postId}`);
  }

  // Comments
  createComment(postId: number, comment: ForumCommentCreate): Observable<ForumComment> {
    return this.http.post<ForumComment>(`${this.apiUrl}/posts/${postId}/comments`, comment);
  }

  updateComment(commentId: number, content: string): Observable<ForumComment> {
    return this.http.put<ForumComment>(`${this.apiUrl}/comments/${commentId}`, { content });
  }

  deleteComment(commentId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/comments/${commentId}`);
  }

  markAsSolution(commentId: number): Observable<ForumComment> {
    return this.http.post<ForumComment>(`${this.apiUrl}/comments/${commentId}/solution`, {});
  }

  // Votes
  votePost(postId: number, voteType: 'UP' | 'DOWN'): Observable<any> {
    return this.http.post(`${this.apiUrl}/posts/${postId}/vote`, { vote_type: voteType });
  }

  voteComment(commentId: number, voteType: 'UP' | 'DOWN'): Observable<any> {
    return this.http.post(`${this.apiUrl}/comments/${commentId}/vote`, { vote_type: voteType });
  }

  // Helper methods
  getReputationLevelName(score: number): string {
    if (score >= 1000) return 'Expert';
    if (score >= 500) return 'Pro';
    return 'Normal';
  }

  getReputationBadgeClass(level: string | null): string {
    if (!level) return '';
    switch (level.toLowerCase()) {
      case 'expert': return 'badge-expert';
      case 'pro': return 'badge-pro';
      default: return 'badge-normal';
    }
  }
}

