import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AdminService, AdminStats, UsersListResponse, UserDetails, RecentTradesResponse, DisputesListResponse, SuspiciousEventListResponse, SuspiciousEvent, SuspiciousEventUpdatePayload } from '../../core/services/admin.service';
import { AuthService, User } from '../../core/services/auth.service';
import { DisputeService, DisputeDetails } from '../../core/services/dispute.service';
import { FormationService, Formation } from '../../core/services/formation.service';
import { Router } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { Chart, ChartConfiguration, ChartData, ChartType, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, BaseChartDirective],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent implements OnInit {
  stats: AdminStats | null = null;
  usersList: UsersListResponse | null = null;
  selectedUser: UserDetails | null = null;
  recentTrades: RecentTradesResponse | null = null;
  disputes: DisputesListResponse | null = null;
  selectedDispute: DisputeDetails | null = null;

  isLoading = false;
  errorMessage = '';
  successMessage = '';

  // Dispute resolution
  resolutionText = '';
  refundToBuyer = false;
  releaseToSeller = false;

  activeTab: 'overview' | 'users' | 'trades' | 'disputes' | 'suspicious' | 'courses' = 'overview';

  // Pagination
  usersSkip = 0;
  usersLimit = 20;
  usersSearch = '';
  usersFilterActive: boolean | null = null;
  usersFilterAdmin: boolean | null = null;

  // Suspicious Events
  suspiciousEvents: SuspiciousEventListResponse | null = null;
  suspiciousSkip = 0;
  suspiciousLimit = 50;
  suspiciousStatus: string | null = null;
  suspiciousMinScore: number | null = null;
  selectedEvent: SuspiciousEvent | null = null;

  // Courses/Formations Management
  coursesList: Formation[] = [];
  youtubeTitle = '';
  youtubeDescription = '';
  youtubeLevel = 'INTERMEDIATE';
  youtubeUrls: string[] = [''];
  youtubeTitles: string[] = [''];
  isCreatingYouTube = false;
  youtubeCreateError: string | null = null;
  youtubeCreateSuccess: string | null = null;
  
  // User assignment
  showUserSelectionModal = false;
  availableUsers: any[] = [];
  selectedUserIds: number[] = [];
  isLoadingUsers = false;
  currentFormationToAssign: Formation | null = null; // Track which formation we're assigning

  constructor(
    private adminService: AdminService,
    private authService: AuthService,
    private disputeService: DisputeService,
    private formationService: FormationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Check if user is admin
    const currentUser = this.authService.getCurrentUser();
    if (!currentUser || !currentUser.is_admin) {
      this.router.navigate(['/dashboard']);
      return;
    }

    this.loadOverview();
  }

  logout(): void {
    this.authService.logout();
  }

  // Chart configurations
  public userGrowthChartData: ChartData<'line'> = {
    labels: [],
    datasets: []
  };
  public userGrowthChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: { color: '#eaecef', font: { size: 12 } }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#848e9c' },
        grid: { color: 'rgba(43, 49, 57, 0.5)' }
      },
      x: {
        ticks: { color: '#848e9c' },
        grid: { color: 'rgba(43, 49, 57, 0.5)' }
      }
    }
  };
  public userGrowthChartType: ChartType = 'line';

  public tradesVolumeChartData: ChartData<'bar'> = {
    labels: [],
    datasets: []
  };
  public tradesVolumeChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: { color: '#eaecef', font: { size: 12 } }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#848e9c' },
        grid: { color: 'rgba(43, 49, 57, 0.5)' }
      },
      x: {
        ticks: { color: '#848e9c' },
        grid: { color: 'rgba(43, 49, 57, 0.5)' }
      }
    }
  };
  public tradesVolumeChartType: ChartType = 'bar';

  public tradeDistributionChartData: ChartData<'doughnut'> = {
    labels: [],
    datasets: []
  };
  public tradeDistributionChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right',
        labels: { color: '#eaecef', font: { size: 12 } }
      }
    }
  };
  public tradeDistributionChartType: ChartType = 'doughnut';

  loadOverview(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.activeTab = 'overview';

    this.adminService.getOverviewStats().subscribe({
      next: (stats) => {
        this.stats = stats;
        this.setupCharts();
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading statistics';
        this.isLoading = false;
      }
    });
  }

  setupCharts(): void {
    if (!this.stats) return;

    // User Growth Chart (last 7 days mock data)
    const last7Days = [];
    const userGrowth = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      last7Days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
      // Mock growth data based on current stats
      const baseGrowth = Math.floor((this.stats.users.new_this_week / 7) * (7 - i));
      userGrowth.push(baseGrowth + Math.floor(Math.random() * 10));
    }

    this.userGrowthChartData = {
      labels: last7Days,
      datasets: [
        {
          label: 'New Users',
          data: userGrowth,
          borderColor: '#F0B90B',
          backgroundColor: 'rgba(240, 185, 11, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    };

    // Trades Volume Chart (last 7 days mock data)
    const tradesOrderbook = [];
    const tradesP2P = [];
    for (let i = 6; i >= 0; i--) {
      tradesOrderbook.push(Math.floor(this.stats.trades.orderbook_total / 7 + Math.random() * 20));
      tradesP2P.push(Math.floor(this.stats.trades.p2p_total / 7 + Math.random() * 15));
    }

    this.tradesVolumeChartData = {
      labels: last7Days,
      datasets: [
        {
          label: 'Orderbook Trades',
          data: tradesOrderbook,
          backgroundColor: '#3b82f6',
          borderColor: '#3b82f6',
          borderWidth: 1
        },
        {
          label: 'P2P Trades',
          data: tradesP2P,
          backgroundColor: '#F0B90B',
          borderColor: '#F0B90B',
          borderWidth: 1
        }
      ]
    };

    // Trade Distribution Chart
    this.tradeDistributionChartData = {
      labels: ['Orderbook Trades', 'P2P Trades', 'Pending Orders'],
      datasets: [
        {
          data: [
            this.stats.trades.orderbook_total,
            this.stats.trades.p2p_total,
            this.stats.orders.pending
          ],
          backgroundColor: ['#3b82f6', '#F0B90B', '#848e9c'],
          borderColor: ['#3b82f6', '#F0B90B', '#848e9c'],
          borderWidth: 2
        }
      ]
    };
  }

  loadUsers(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.activeTab = 'users';

    this.adminService.getUsers(
      this.usersSkip,
      this.usersLimit,
      this.usersSearch || undefined,
      this.usersFilterActive !== null ? this.usersFilterActive : undefined,
      this.usersFilterAdmin !== null ? this.usersFilterAdmin : undefined
    ).subscribe({
      next: (response) => {
        this.usersList = response;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading users';
        this.isLoading = false;
      }
    });
  }

  loadUserDetails(userId: number): void {
    this.adminService.getUserDetails(userId).subscribe({
      next: (details) => {
        this.selectedUser = details;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading user details';
      }
    });
  }

  toggleUserActive(user: User): void {
    if (!confirm(`Are you sure you want to ${user.is_active ? 'deactivate' : 'activate'} this user?`)) {
      return;
    }

    this.adminService.toggleUserActive(user.id).subscribe({
      next: () => {
        if (this.usersList) {
          const userIndex = this.usersList.users.findIndex(u => u.id === user.id);
          if (userIndex !== -1) {
            this.usersList.users[userIndex].is_active = !this.usersList.users[userIndex].is_active;
          }
        }
        this.selectedUser = null;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error updating user';
      }
    });
  }

  toggleUserAdmin(user: User): void {
    if (!confirm(`Are you sure you want to ${user.is_admin ? 'remove' : 'grant'} admin privileges for this user?`)) {
      return;
    }

    this.adminService.toggleUserAdmin(user.id).subscribe({
      next: () => {
        if (this.usersList) {
          const userIndex = this.usersList.users.findIndex(u => u.id === user.id);
          if (userIndex !== -1) {
            this.usersList.users[userIndex].is_admin = !this.usersList.users[userIndex].is_admin;
          }
        }
        this.selectedUser = null;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error updating user';
      }
    });
  }

  loadRecentTrades(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.activeTab = 'trades';

    this.adminService.getRecentTrades(0, 50).subscribe({
      next: (trades) => {
        this.recentTrades = trades;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading trades';
        this.isLoading = false;
      }
    });
  }

  loadDisputes(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.activeTab = 'disputes';

    this.adminService.getDisputes(0, 50).subscribe({
      next: (disputes) => {
        this.disputes = disputes;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading disputes';
        this.isLoading = false;
      }
    });
  }

  searchUsers(): void {
    this.usersSkip = 0;
    this.loadUsers();
  }

  nextPageUsers(): void {
    if (this.usersList && this.usersSkip + this.usersLimit < this.usersList.total) {
      this.usersSkip += this.usersLimit;
      this.loadUsers();
    }
  }

  prevPageUsers(): void {
    if (this.usersSkip >= this.usersLimit) {
      this.usersSkip -= this.usersLimit;
      this.loadUsers();
    }
  }

  // Suspicious Events
  loadSuspiciousEvents(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.activeTab = 'suspicious';

    this.adminService.getSuspiciousEvents(
      this.suspiciousSkip,
      this.suspiciousLimit,
      this.suspiciousStatus || undefined,
      this.suspiciousMinScore || undefined
    ).subscribe({
      next: (response) => {
        this.suspiciousEvents = response;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading suspicious alerts';
        this.isLoading = false;
      }
    });
  }

  viewEventDetails(event: SuspiciousEvent): void {
    this.selectedEvent = event;
  }

  closeEventDetails(): void {
    this.selectedEvent = null;
  }

  updateEventStatus(event: SuspiciousEvent, newStatus: string, notes?: string): void {
    const payload: SuspiciousEventUpdatePayload = {
      status: newStatus
    };
    if (notes) {
      payload.admin_notes = notes;
    }

    this.adminService.updateSuspiciousEvent(event.id, payload).subscribe({
      next: (updated) => {
        // Update in list
        if (this.suspiciousEvents) {
          const index = this.suspiciousEvents.events.findIndex(e => e.id === event.id);
          if (index !== -1) {
            this.suspiciousEvents.events[index] = updated;
          }
        }
        this.selectedEvent = null;
        this.loadSuspiciousEvents(); // Refresh list
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error updating event';
      }
    });
  }

  filterSuspiciousEvents(): void {
    this.suspiciousSkip = 0;
    this.loadSuspiciousEvents();
  }

  nextPageSuspicious(): void {
    if (this.suspiciousEvents && this.suspiciousSkip + this.suspiciousLimit < this.suspiciousEvents.total) {
      this.suspiciousSkip += this.suspiciousLimit;
      this.loadSuspiciousEvents();
    }
  }

  prevPageSuspicious(): void {
    if (this.suspiciousSkip >= this.suspiciousLimit) {
      this.suspiciousSkip -= this.suspiciousLimit;
      this.loadSuspiciousEvents();
    }
  }

  getScoreColor(score: number): string {
    if (score >= 80) return '#F6465D'; // Red - Critical
    if (score >= 60) return '#F0B90B'; // Yellow - High
    if (score >= 40) return '#FCD535'; // Light yellow - Medium
    return '#848E9C'; // Gray - Low
  }

  getRiskLevel(score: number): string {
    if (score >= 80) return 'critical';
    if (score >= 60) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  }

  getStatusLabel(status: string): string {
    const labels: { [key: string]: string } = {
      'OPEN': '🔴 Open',
      'REVIEWED': '🟡 Under Review',
      'CONFIRMED': 'Confirmed Fraud',
      'FALSE_POSITIVE': '⚪ False Positive'
    };
    return labels[status] || status;
  }

  getAlertsByStatus(status: string): number {
    if (!this.suspiciousEvents) return 0;
    return this.suspiciousEvents.events.filter(e => e.status === status).length;
  }

  clearAlertsFilters(): void {
    this.suspiciousStatus = null;
    this.suspiciousMinScore = null;
    this.filterSuspiciousEvents();
  }

  // Dispute Management
  viewDisputeDetails(disputeId: number): void {
    this.errorMessage = '';
    this.successMessage = '';
    this.isLoading = true;

    this.disputeService.getDisputeDetails(disputeId).subscribe({
      next: (details) => {
        this.selectedDispute = details;
        this.resolutionText = '';
        this.refundToBuyer = false;
        this.releaseToSeller = false;
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error loading dispute details';
        this.isLoading = false;
      }
    });
  }

  closeDisputeDetails(): void {
    this.selectedDispute = null;
    this.resolutionText = '';
    this.refundToBuyer = false;
    this.releaseToSeller = false;
  }

  resolveDispute(): void {
    if (!this.selectedDispute || !this.resolutionText.trim()) {
      this.errorMessage = 'Please provide a resolution explanation';
      return;
    }

    if (!this.refundToBuyer && !this.releaseToSeller) {
      this.errorMessage = 'Please select a resolution action (refund buyer or release to seller)';
      return;
    }

    if (!confirm('Are you sure you want to resolve this dispute? This action cannot be undone.')) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.disputeService.resolveDispute(this.selectedDispute.dispute.id, {
      resolution: this.resolutionText,
      refund_to_buyer: this.refundToBuyer,
      release_to_seller: this.releaseToSeller
    }).subscribe({
      next: () => {
        this.successMessage = 'Dispute resolved successfully';
        this.closeDisputeDetails();
        this.loadDisputes(); // Refresh list
        this.isLoading = false;
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error resolving dispute';
        this.isLoading = false;
      }
    });
  }

  getDisputeStatusColor(status: string): string {
    return this.disputeService.getStatusColor(status);
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

  getDisputesByStatus(status: string): number {
    if (!this.disputes) return 0;
    return this.disputes.disputes.filter(d => d.status === status).length;
  }

  // ==================== COURSES MANAGEMENT ====================

  loadCourses(): void {
    this.activeTab = 'courses';
    this.isLoading = true;
    this.formationService.getFormations().subscribe({
      next: (formations) => {
        this.coursesList = formations;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading courses:', error);
        this.errorMessage = 'Erreur lors du chargement des formations';
        this.isLoading = false;
      }
    });
    
    // Reset form if it's empty
    if (this.youtubeUrls.length === 0) {
      this.youtubeUrls = [''];
      this.youtubeTitles = [''];
    }
  }

  addYouTubeUrl(): void {
    this.youtubeUrls.push('');
    this.youtubeTitles.push('');
  }

  removeYouTubeUrl(index: number): void {
    if (this.youtubeUrls.length > 1) {
      this.youtubeUrls.splice(index, 1);
      this.youtubeTitles.splice(index, 1);
    }
  }

  canCreateYouTubeFormation(): boolean {
    const title = this.youtubeTitle.trim();
    const urls = this.youtubeUrls.filter(u => u.trim() !== '');
    return title.length > 0 && urls.length > 0 && !this.isCreatingYouTube;
  }

  createYouTubeFormation(): void {
    const title = this.youtubeTitle.trim();
    const urls = this.youtubeUrls.filter(url => url.trim() !== '');
    
    if (!title) {
      this.youtubeCreateError = 'Veuillez entrer un titre pour la formation';
      return;
    }
    
    if (urls.length === 0) {
      this.youtubeCreateError = 'Veuillez entrer au moins une URL YouTube';
      return;
    }
    
    // Validate YouTube URLs
    const youtubeUrlPattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    for (const url of urls) {
      if (!youtubeUrlPattern.test(url)) {
        this.youtubeCreateError = `URL YouTube invalide: ${url}`;
        return;
      }
    }
    
    this.isCreatingYouTube = true;
    this.youtubeCreateError = null;
    this.youtubeCreateSuccess = null;
    
    const titles = this.youtubeTitles.filter((t, i) => i < urls.length && t.trim() !== '');
    
    this.formationService.createYouTubeFormation({
      title: title,
      description: this.youtubeDescription.trim() || undefined,
      level: this.youtubeLevel,
      video_urls: urls,
      video_titles: titles.length > 0 ? titles : undefined,
      user_ids: this.selectedUserIds.length > 0 ? this.selectedUserIds : undefined
    }).subscribe({
      next: (result) => {
        this.youtubeCreateSuccess = `Formation created successfully! ${result.videos_count} videos added.`;
        this.isCreatingYouTube = false;
        
        // Close modal and reset
        this.showUserSelectionModal = false;
        this.selectedUserIds = [];
        
        // Reload courses after 2 seconds
        setTimeout(() => {
          this.loadCourses();
          // Reset form
          this.youtubeTitle = '';
          this.youtubeDescription = '';
          this.youtubeLevel = 'INTERMEDIATE';
          this.youtubeUrls = [''];
          this.youtubeTitles = [''];
          this.youtubeCreateSuccess = null;
        }, 2000);
      },
      error: (error) => {
        console.error('Error creating YouTube formation:', error);
        const errorMessage = error.error?.detail || 'Error creating the formation';
        this.youtubeCreateError = errorMessage;
        this.isCreatingYouTube = false;
      }
    });
  }

  openUserSelectionModal(formation?: Formation): void {
    this.currentFormationToAssign = formation || null; // null = creating new formation, formation = assigning existing
    this.showUserSelectionModal = true;
    this.selectedUserIds = [];
    this.loadAvailableUsers();
  }

  closeUserSelectionModal(): void {
    this.showUserSelectionModal = false;
    this.selectedUserIds = [];
    this.currentFormationToAssign = null;
  }

  loadAvailableUsers(): void {
    this.isLoadingUsers = true;
    this.availableUsers = [];
    // Backend limit is max 100, so we'll fetch up to 100 users
    this.adminService.getUsers(0, 100).subscribe({
      next: (response) => {
        console.log('Users loaded:', response);
        // Show all users (including admins) - admin can decide who to assign to
        this.availableUsers = response.users || [];
        this.isLoadingUsers = false;
        console.log('Available users count:', this.availableUsers.length);
      },
      error: (error) => {
        console.error('Error loading users:', error);
        this.isLoadingUsers = false;
        // Show error message to user
        this.youtubeCreateError = 'Error loading users. Please check the browser console for details.';
        setTimeout(() => {
          this.youtubeCreateError = null;
        }, 5000);
      }
    });
  }

  toggleUserSelection(userId: number): void {
    const index = this.selectedUserIds.indexOf(userId);
    if (index > -1) {
      this.selectedUserIds.splice(index, 1);
    } else {
      this.selectedUserIds.push(userId);
    }
  }

  isUserSelected(userId: number): boolean {
    return this.selectedUserIds.includes(userId);
  }

  confirmUserSelection(): void {
    // Store the selected user IDs before closing the modal
    const userIdsToAssign = [...this.selectedUserIds];
    const formationToAssign = this.currentFormationToAssign;
    
    // Close the modal (this will reset selectedUserIds)
    this.closeUserSelectionModal();
    
    if (formationToAssign) {
      // Assign existing formation to users
      this.selectedUserIds = userIdsToAssign;
      this.assignExistingFormationToUsers(formationToAssign);
    } else {
      // Create new formation with the stored user IDs
      this.selectedUserIds = userIdsToAssign;
      this.createYouTubeFormation();
      // After the API call, selectedUserIds will be reset in the success handler
    }
  }

  assignExistingFormationToUsers(formation: Formation): void {
    if (this.selectedUserIds.length === 0) {
      this.errorMessage = 'Please select at least one user to assign the formation to.';
      setTimeout(() => {
        this.errorMessage = '';
      }, 3000);
      return;
    }

    this.isCreatingYouTube = true;
    this.youtubeCreateError = null;
    this.youtubeCreateSuccess = null;

    this.formationService.assignFormationToUsers(formation.id, this.selectedUserIds).subscribe({
      next: (result) => {
        this.isCreatingYouTube = false;
        this.youtubeCreateSuccess = `Formation "${formation.title}" assigned to ${result.assigned_count} user(s) successfully!`;
        this.selectedUserIds = [];
        
        setTimeout(() => {
          this.youtubeCreateSuccess = null;
        }, 3000);
      },
      error: (error) => {
        console.error('Error assigning formation to users:', error);
        this.isCreatingYouTube = false;
        this.youtubeCreateError = error.error?.detail || 'Error assigning formation to users';
        this.selectedUserIds = [];
        setTimeout(() => {
          this.youtubeCreateError = null;
        }, 5000);
      }
    });
  }

  toggleCourseActive(course: Formation): void {
    this.formationService.updateFormation(course.id, { is_active: !course.is_active }).subscribe({
      next: (updatedCourse) => {
        const index = this.coursesList.findIndex(c => c.id === course.id);
        if (index !== -1) {
          this.coursesList[index] = updatedCourse;
        }
      },
      error: (error) => {
        console.error('Error toggling course status:', error);
        this.errorMessage = 'Erreur lors de la modification du statut';
      }
    });
  }

  deleteCourse(course: Formation): void {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer la formation "${course.title}" ?`)) {
      return;
    }
    
    this.formationService.deleteFormation(course.id).subscribe({
      next: () => {
        this.coursesList = this.coursesList.filter(c => c.id !== course.id);
        this.successMessage = 'Formation supprimée avec succès';
        setTimeout(() => {
          this.successMessage = '';
        }, 3000);
      },
      error: (error) => {
        console.error('Error deleting course:', error);
        this.errorMessage = 'Erreur lors de la suppression de la formation';
      }
    });
  }

  // Expose Math to template
  Math = Math;
}

