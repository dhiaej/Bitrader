import { Component, signal, OnInit, OnDestroy } from '@angular/core';
import { RouterOutlet, RouterModule, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService, User } from './core/services/auth.service';
import { MarketTickerComponent } from './shared/components/market-ticker/market-ticker.component';
import { Subscription, filter } from 'rxjs';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterModule, CommonModule, MarketTickerComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit, OnDestroy {
  protected readonly title = signal('frontend');
  currentUser: User | null = null;
  showNavbar = false;
  private userSub?: Subscription;
  private routerSub?: Subscription;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Subscribe to user changes
    this.userSub = this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      this.updateNavbarVisibility();
    });

    // Subscribe to route changes to hide navbar on login/register
    this.routerSub = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.updateNavbarVisibility();
      });

    // Initial check
    this.updateNavbarVisibility();
  }

  ngOnDestroy(): void {
    this.userSub?.unsubscribe();
    this.routerSub?.unsubscribe();
  }

  private updateNavbarVisibility(): void {
    const currentRoute = this.router.url;
    // Hide navbar on login, register, and admin pages
    this.showNavbar = this.currentUser !== null &&
                      !currentRoute.includes('/login') &&
                      !currentRoute.includes('/register') &&
                      !currentRoute.includes('/admin');
  }

  logout(): void {
    this.authService.logout();
  }
}
