import { Component, ElementRef, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnDestroy {
  loginForm: FormGroup;
  faceLoginForm: FormGroup;
  errorMessage = '';
  isLoading = false;

  // Face login
  showFaceLogin = false;
  isFaceCameraActive = false;
  isFaceLoggingIn = false;
  faceLoginError = '';
  private faceStream: MediaStream | null = null;

  @ViewChild('faceVideo') faceVideoRef?: ElementRef<HTMLVideoElement>;
  @ViewChild('faceCanvas') faceCanvasRef?: ElementRef<HTMLCanvasElement>;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required]],
      password: ['', [Validators.required]]
    });

    this.faceLoginForm = this.fb.group({
      username: ['', [Validators.required]]
    });
  }

  ngOnDestroy(): void {
    this.stopFaceCamera();
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    const { username, password } = this.loginForm.value;

    this.authService.login(username, password).subscribe({
      next: () => {
        // Wait for user data to load and check if admin
        setTimeout(() => {
          const currentUser = this.authService.getCurrentUser();
          if (currentUser?.is_admin) {
            this.router.navigate(['/admin']);
          } else {
            this.router.navigate(['/dashboard']);
          }
        }, 500); // Small delay to ensure user data is loaded
      },
      error: (error) => {
        this.isLoading = false;
        this.errorMessage = error.error?.detail || 'Login failed. Please try again.';
      }
    });
  }

  toggleFaceLogin(): void {
    this.showFaceLogin = !this.showFaceLogin;
    this.errorMessage = '';
    this.faceLoginError = '';
    if (!this.showFaceLogin) {
      this.stopFaceCamera();
    }
  }

  async startFaceCamera(): Promise<void> {
    if (!('mediaDevices' in navigator) || !navigator.mediaDevices?.getUserMedia) {
      this.faceLoginError = 'Your browser does not support the camera.';
      return;
    }

    try {
      this.faceStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 } }
      });
      this.isFaceCameraActive = true;
      this.faceLoginError = '';

      setTimeout(() => {
        if (this.faceVideoRef?.nativeElement) {
          this.faceVideoRef.nativeElement.srcObject = this.faceStream;
        }
      }, 100);
    } catch (error) {
      console.error('Failed to start face camera', error);
      this.faceLoginError = 'Unable to access the camera. Please check your permissions.';
      this.isFaceCameraActive = false;
    }
  }

  stopFaceCamera(): void {
    if (this.faceStream) {
      this.faceStream.getTracks().forEach(track => track.stop());
      this.faceStream = null;
    }
    this.isFaceCameraActive = false;
  }

  captureFaceLogin(): void {
    if (!this.isFaceCameraActive || this.isFaceLoggingIn || this.faceLoginForm.invalid) {
      if (this.faceLoginForm.invalid) {
        this.faceLoginError = 'Please enter your username.';
      }
      return;
    }

    const videoEl = this.faceVideoRef?.nativeElement;
    const canvasEl = this.faceCanvasRef?.nativeElement;
    if (!videoEl || !canvasEl) {
      this.faceLoginError = 'Camera not available.';
      return;
    }

    const width = videoEl.videoWidth || 640;
    const height = videoEl.videoHeight || 480;
    canvasEl.width = width;
    canvasEl.height = height;

    const ctx = canvasEl.getContext('2d');
    if (!ctx) {
      this.faceLoginError = 'Unable to capture the image.';
      return;
    }

    ctx.drawImage(videoEl, 0, 0, width, height);
    canvasEl.toBlob((blob) => {
      if (!blob) {
        this.faceLoginError = 'Capture failed. Try again.';
        return;
      }

      this.isFaceLoggingIn = true;
      this.faceLoginError = '';

      const username = this.faceLoginForm.get('username')?.value;

      this.authService.faceLogin(username, blob).subscribe({
        next: () => {
          this.isFaceLoggingIn = false;
          this.stopFaceCamera();
          // Wait for user data to load and check if admin
          setTimeout(() => {
            const currentUser = this.authService.getCurrentUser();
            if (currentUser?.is_admin) {
              this.router.navigate(['/admin']);
            } else {
              this.router.navigate(['/dashboard']);
            }
          }, 500); // Small delay to ensure user data is loaded
        },
        error: (error) => {
          this.isFaceLoggingIn = false;
          this.faceLoginError = error.error?.detail || error.message || 'Face login failed.';
        }
      });
    }, 'image/jpeg', 0.9);
  }
}
