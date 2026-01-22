import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DisputeService, DisputeListResponse, DisputeResponse } from '../../core/services/dispute.service';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-disputes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './disputes.component.html',
  styleUrls: ['./disputes.component.scss']
})
export class DisputesComponent implements OnInit {
  disputes: DisputeListResponse | null = null;
  selectedDispute: DisputeResponse | null = null;

  isLoading = false;
  errorMessage = '';
  successMessage = '';

  // Add evidence form
  newEvidence = '';
  addingEvidence = false;

  constructor(
    private disputeService: DisputeService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadDisputes();
  }

  loadDisputes(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.disputeService.getMyDisputes().subscribe({
      next: (response) => {
        this.disputes = response;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading disputes';
        this.isLoading = false;
      }
    });
  }

  viewDetails(dispute: DisputeResponse): void {
    this.selectedDispute = dispute;
    this.newEvidence = '';
  }

  closeDetails(): void {
    this.selectedDispute = null;
    this.newEvidence = '';
    this.addingEvidence = false;
  }

  addEvidence(): void {
    if (!this.selectedDispute || !this.newEvidence.trim()) {
      return;
    }

    this.addingEvidence = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.disputeService.addEvidence(this.selectedDispute.id, {
      evidence: this.newEvidence
    }).subscribe({
      next: (updated) => {
        this.successMessage = 'Evidence added successfully';
        this.newEvidence = '';
        this.addingEvidence = false;

        // Update the dispute in the list
        if (this.disputes) {
          const index = this.disputes.disputes.findIndex(d => d.id === updated.id);
          if (index !== -1) {
            this.disputes.disputes[index] = updated;
          }
        }
        this.selectedDispute = updated;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error adding evidence';
        this.addingEvidence = false;
      }
    });
  }

  cancelDispute(dispute: DisputeResponse): void {
    if (!confirm('Are you sure you want to cancel this dispute? This action cannot be undone.')) {
      return;
    }

    this.errorMessage = '';
    this.successMessage = '';

    this.disputeService.cancelDispute(dispute.id).subscribe({
      next: () => {
        this.successMessage = 'Dispute cancelled successfully';
        this.closeDetails();
        this.loadDisputes(); // Refresh list
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error cancelling dispute';
      }
    });
  }

  getStatusColor(status: string): string {
    return this.disputeService.getStatusColor(status);
  }

  getStatusText(status: string): string {
    return this.disputeService.getStatusText(status);
  }

  parseEvidence(evidence: string | undefined): any[] {
    if (!evidence) return [];
    try {
      const parsed = JSON.parse(evidence);
      return Array.isArray(parsed) ? parsed : [evidence];
    } catch {
      return [evidence];
    }
  }

  getCurrentUserId(): number | null {
    const user = this.authService.getCurrentUser();
    return user ? user.id : null;
  }

  canAddEvidence(dispute: DisputeResponse): boolean {
    return dispute.status === 'OPEN' || dispute.status === 'IN_REVIEW';
  }

  canCancel(dispute: DisputeResponse): boolean {
    const currentUserId = this.getCurrentUserId();
    return dispute.status === 'OPEN' && dispute.filed_by === currentUserId;
  }
}
