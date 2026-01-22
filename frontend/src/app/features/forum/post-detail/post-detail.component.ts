import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ForumService, ForumPostDetail, ForumComment } from '../../../core/services/forum.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-post-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, ReactiveFormsModule],
  templateUrl: './post-detail.component.html',
  styleUrls: ['./post-detail.component.scss']
})
export class PostDetailComponent implements OnInit {
  postId!: number;
  post: ForumPostDetail | null = null;
  loading = true;
  error: string | null = null;
  
  commentForm: FormGroup;
  replyForms: { [key: number]: FormGroup } = {};
  showReplyForm: { [key: number]: boolean } = {};
  
  isSubmittingComment = false;
  editingCommentId: number | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private forumService: ForumService,
    private authService: AuthService,
    private fb: FormBuilder
  ) {
    this.commentForm = this.fb.group({
      content: ['', [Validators.required, Validators.minLength(1)]]
    });
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      this.postId = +params['id'];
      this.loadPost();
    });
  }

  loadPost(): void {
    this.loading = true;
    this.error = null;

    this.forumService.getPost(this.postId).subscribe({
      next: (post) => {
        this.post = post;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load post';
        console.error('Error loading post:', err);
        this.loading = false;
      }
    });
  }

  submitComment(): void {
    if (this.commentForm.invalid || this.isSubmittingComment) return;

    this.isSubmittingComment = true;
    const content = this.commentForm.get('content')?.value;

    this.forumService.createComment(this.postId, { content }).subscribe({
      next: () => {
        this.commentForm.reset();
        this.loadPost();
        this.isSubmittingComment = false;
      },
      error: (err) => {
        console.error('Error creating comment:', err);
        this.isSubmittingComment = false;
      }
    });
  }

  toggleReply(commentId: number): void {
    if (!this.replyForms[commentId]) {
      this.replyForms[commentId] = this.fb.group({
        content: ['', [Validators.required, Validators.minLength(1)]]
      });
    }
    this.showReplyForm[commentId] = !this.showReplyForm[commentId];
  }

  submitReply(parentCommentId: number): void {
    const form = this.replyForms[parentCommentId];
    if (!form || form.invalid) return;

    const content = form.get('content')?.value;
    this.isSubmittingComment = true;

    this.forumService.createComment(this.postId, { content, parent_comment_id: parentCommentId }).subscribe({
      next: () => {
        form.reset();
        this.showReplyForm[parentCommentId] = false;
        this.loadPost();
        this.isSubmittingComment = false;
      },
      error: (err) => {
        console.error('Error creating reply:', err);
        this.isSubmittingComment = false;
      }
    });
  }

  votePost(voteType: 'UP' | 'DOWN'): void {
    if (!this.post) return;

    this.forumService.votePost(this.postId, voteType).subscribe({
      next: () => {
        this.loadPost();
      },
      error: (err) => {
        console.error('Error voting:', err);
      }
    });
  }

  voteComment(commentId: number, voteType: 'UP' | 'DOWN'): void {
    this.forumService.voteComment(commentId, voteType).subscribe({
      next: () => {
        this.loadPost();
      },
      error: (err) => {
        console.error('Error voting:', err);
      }
    });
  }

  markAsSolution(commentId: number): void {
    if (!this.post || this.post.author.id !== this.getCurrentUserId()) return;

    this.forumService.markAsSolution(commentId).subscribe({
      next: () => {
        this.loadPost();
      },
      error: (err) => {
        console.error('Error marking solution:', err);
      }
    });
  }

  deletePost(): void {
    if (!confirm('Are you sure you want to delete this post?')) return;

    this.forumService.deletePost(this.postId).subscribe({
      next: () => {
        this.router.navigate(['/forum/category', this.post?.category_id]);
      },
      error: (err) => {
        console.error('Error deleting post:', err);
      }
    });
  }

  deleteComment(commentId: number): void {
    if (!confirm('Are you sure you want to delete this comment?')) return;

    this.forumService.deleteComment(commentId).subscribe({
      next: () => {
        this.loadPost();
      },
      error: (err) => {
        console.error('Error deleting comment:', err);
      }
    });
  }

  canEditPost(): boolean {
    if (!this.post) return false;
    const user = this.authService.getCurrentUser();
    return user?.id === this.post.author.id || user?.is_admin === true;
  }

  canDeletePost(): boolean {
    return this.canEditPost();
  }

  canEditComment(comment: ForumComment): boolean {
    const user = this.authService.getCurrentUser();
    return user?.id === comment.author.id || user?.is_admin === true;
  }

  canMarkSolution(comment: ForumComment): boolean {
    if (!this.post) return false;
    const user = this.authService.getCurrentUser();
    return user?.id === this.post.author.id && !comment.is_solution;
  }

  getCurrentUserId(): number | null {
    return this.authService.getCurrentUser()?.id || null;
  }

  get currentUser() {
    return this.authService.getCurrentUser();
  }
}

