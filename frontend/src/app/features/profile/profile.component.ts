import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { UserService } from '../../core/services/user.service';
import { AuthService, User } from '../../core/services/auth.service';
import { ReputationService, ReputationProfile } from '../../core/services/reputation.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit, OnDestroy {
  profileForm: FormGroup;
  isSaving = false;
  saveMessage = '';
  errorMessage = '';

  avatarPreview = '';
  selectedAvatar: File | null = null;
  uploadMessage = '';
  isUploading = false;
  reputationProfile: ReputationProfile | null = null;
  isReputationLoading = false;
  reputationError = '';
  isFaceCameraActive = false;
  isRegisteringFace = false;
  faceRegisterMessage = '';
  faceRegisterError = '';
  private faceStream: MediaStream | null = null;

  @ViewChild('faceVideo') faceVideoRef?: ElementRef<HTMLVideoElement>;
  @ViewChild('faceCanvas') faceCanvasRef?: ElementRef<HTMLCanvasElement>;

  constructor(
    private fb: FormBuilder,
    private userService: UserService,
    private authService: AuthService,
    private reputationService: ReputationService
  ) {
    this.profileForm = this.fb.group({
      username: [{ value: '', disabled: true }],
      full_name: [''],
      email: ['', [Validators.required, Validators.email]]
    });
  }

  ngOnInit(): void {
    this.loadProfile();
    this.loadReputation();
  }

  ngOnDestroy(): void {
    this.stopFaceCamera();
  }

  private loadProfile(): void {
    this.userService.getProfile().subscribe({
      next: (user) => {
        this.profileForm.patchValue({
          username: user.username,
          full_name: user.full_name || '',
          email: user.email
        });
        this.avatarPreview = this.resolveAvatar(user);
        this.errorMessage = '';
      },
      error: () => {
        this.errorMessage = 'Unable to load your profile.';
      }
    });
  }

  private loadReputation(): void {
    this.isReputationLoading = true;
    this.reputationService.getMyProfile().subscribe({
      next: (profile) => {
        this.reputationProfile = profile;
        this.isReputationLoading = false;
      },
      error: () => {
        this.reputationError = 'Unable to load your reputation.';
        this.isReputationLoading = false;
      }
    });
  }

  private resolveAvatar(user: User): string {
    const resolved = this.userService.resolveAvatarUrl(user.avatar_url);
    if (resolved) {
      return resolved;
    }
    const initials = encodeURIComponent(user.full_name || user.username);
    return `https://ui-avatars.com/api/?name=${initials}&background=0D8ABC&color=FFFFFF&size=128`;
  }

  onSubmit(): void {
    if (this.profileForm.invalid) {
      return;
    }
    this.isSaving = true;
    this.saveMessage = '';
    this.errorMessage = '';

    const payload = {
      full_name: this.profileForm.get('full_name')?.value,
      email: this.profileForm.get('email')?.value
    };

    this.userService.updateProfile(payload).subscribe({
      next: (user) => {
        this.isSaving = false;
        this.saveMessage = 'Profile updated successfully.';
        this.avatarPreview = this.resolveAvatar(user);
        this.authService.loadCurrentUser();
        this.loadReputation();
      },
      error: (error) => {
        this.isSaving = false;
        this.errorMessage = error.error?.detail || 'Update failed.';
      }
    });
  }

  onAvatarSelected(event: Event): void {
    const target = event.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) {
      this.selectedAvatar = null;
      return;
    }
    this.selectedAvatar = target.files[0];

    const reader = new FileReader();
    reader.onload = () => {
      this.avatarPreview = reader.result as string;
    };
    reader.readAsDataURL(this.selectedAvatar);
  }

  uploadAvatar(): void {
    if (!this.selectedAvatar) {
      return;
    }
    this.isUploading = true;
    this.uploadMessage = '';
    this.errorMessage = '';

    this.userService.uploadAvatar(this.selectedAvatar).subscribe({
      next: (user) => {
        this.isUploading = false;
        this.uploadMessage = 'Profile picture updated.';
        this.avatarPreview = this.resolveAvatar(user);
        this.selectedAvatar = null;
        this.authService.loadCurrentUser();
        this.loadReputation();
      },
      error: (error) => {
        this.isUploading = false;
        this.errorMessage = error.error?.detail || 'Upload failed.';
      }
    });
  }

  formatReviewDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  async toggleFaceCamera(): Promise<void> {
    if (this.isFaceCameraActive) {
      this.stopFaceCamera();
      return;
    }

    if (!('mediaDevices' in navigator) || !navigator.mediaDevices?.getUserMedia) {
      this.faceRegisterError = 'Your browser does not support the camera.';
      return;
    }

    try {
      this.faceStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 } }
      });
      this.isFaceCameraActive = true;
      this.faceRegisterError = '';
      if (this.faceVideoRef?.nativeElement) {
        this.faceVideoRef.nativeElement.srcObject = this.faceStream;
      }
    } catch (error) {
      console.error('Failed to start face camera', error);
      this.faceRegisterError = 'Unable to access the camera.';
      this.isFaceCameraActive = false;
    }
  }

  private stopFaceCamera(): void {
    if (this.faceStream) {
      this.faceStream.getTracks().forEach(track => track.stop());
      this.faceStream = null;
    }
    this.isFaceCameraActive = false;
  }

  captureFaceRegistration(): void {
    if (!this.isFaceCameraActive || this.isRegisteringFace) {
      return;
    }

    const videoEl = this.faceVideoRef?.nativeElement;
    const canvasEl = this.faceCanvasRef?.nativeElement;
    if (!videoEl || !canvasEl) {
      this.faceRegisterError = 'Camera not available.';
      return;
    }

    const width = videoEl.videoWidth || 640;
    const height = videoEl.videoHeight || 480;
    canvasEl.width = width;
    canvasEl.height = height;

    const ctx = canvasEl.getContext('2d');
    if (!ctx) {
      this.faceRegisterError = 'Unable to capture the image.';
      return;
    }

    ctx.drawImage(videoEl, 0, 0, width, height);
    canvasEl.toBlob((blob) => {
      if (!blob) {
        this.faceRegisterError = 'Capture failed. Try again.';
        return;
      }

      this.isRegisteringFace = true;
      this.faceRegisterError = '';
      this.faceRegisterMessage = '';

      this.authService.registerFace(blob).subscribe({
        next: (response) => {
          this.isRegisteringFace = false;
          this.faceRegisterMessage = response.message;
          this.authService.loadCurrentUser();
        },
        error: (error) => {
          this.isRegisteringFace = false;
          this.faceRegisterError = error.error?.detail || error.message || 'Registration failed.';
        }
      });
    }, 'image/jpeg', 0.9);
  }
}

