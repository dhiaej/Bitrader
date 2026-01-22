import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { ForumService, ForumCategory, ForumPost } from '../../../core/services/forum.service';

@Component({
  selector: 'app-post-form',
  standalone: true,
  imports: [CommonModule, RouterModule, ReactiveFormsModule, FormsModule],
  templateUrl: './post-form.component.html',
  styleUrls: ['./post-form.component.scss']
})
export class PostFormComponent implements OnInit {
  postForm: FormGroup;
  categories: ForumCategory[] = [];
  categoryId: number | null = null;
  postId: number | null = null;
  isEditMode = false;
  loading = false;
  error: string | null = null;
  tagsInput = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private forumService: ForumService,
    private fb: FormBuilder
  ) {
    this.postForm = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(200)]],
      content: ['', [Validators.required, Validators.minLength(10)]],
      category_id: [null, Validators.required],
      tags: [[]]
    });
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.postId = +params['id'];
        this.isEditMode = true;
        this.loadPost();
      } else if (params['categoryId']) {
        this.categoryId = +params['categoryId'];
        this.postForm.patchValue({ category_id: this.categoryId });
      }
      this.loadCategories();
    });
  }

  loadCategories(): void {
    this.forumService.getCategories().subscribe({
      next: (categories) => {
        this.categories = categories;
      },
      error: (err) => {
        console.error('Error loading categories:', err);
      }
    });
  }

  loadPost(): void {
    if (!this.postId) return;

    this.loading = true;
    this.forumService.getPost(this.postId).subscribe({
      next: (post) => {
        this.postForm.patchValue({
          title: post.title,
          content: post.content,
          category_id: post.category_id
        });
        if (post.tags && post.tags.length > 0) {
          this.tagsInput = post.tags.join(', ');
          this.postForm.patchValue({ tags: post.tags });
        }
        this.categoryId = post.category_id;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load post';
        console.error('Error loading post:', err);
        this.loading = false;
      }
    });
  }

  onTagsChange(): void {
    const tags = this.tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
    this.postForm.patchValue({ tags });
  }

  onSubmit(): void {
    if (this.postForm.invalid || this.loading) return;

    this.loading = true;
    this.error = null;

    const formValue = this.postForm.value;

    if (this.isEditMode && this.postId) {
      this.forumService.updatePost(this.postId, formValue).subscribe({
        next: (post) => {
          this.router.navigate(['/forum/post', post.id]);
        },
        error: (err) => {
          this.error = 'Failed to update post';
          console.error('Error updating post:', err);
          this.loading = false;
        }
      });
    } else {
      this.forumService.createPost(formValue).subscribe({
        next: (post) => {
          this.router.navigate(['/forum/post', post.id]);
        },
        error: (err) => {
          this.error = err.error?.detail || 'Failed to create post';
          console.error('Error creating post:', err);
          this.loading = false;
        }
      });
    }
  }

  cancel(): void {
    if (this.isEditMode && this.postId) {
      this.router.navigate(['/forum/post', this.postId]);
    } else if (this.categoryId) {
      this.router.navigate(['/forum/category', this.categoryId]);
    } else {
      this.router.navigate(['/forum']);
    }
  }
}

