import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () => import('./auth/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'register',
    loadComponent: () => import('./auth/register/register.component').then(m => m.RegisterComponent)
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'orderbook',
    canActivate: [authGuard],
    loadComponent: () => import('./features/orderbook/orderbook.component').then(m => m.OrderbookComponent)
  },
  {
    path: 'p2p',
    canActivate: [authGuard],
    loadComponent: () => import('./features/p2p/p2p.component').then(m => m.P2pComponent)
  },
  {
    path: 'wallet',
    canActivate: [authGuard],
    loadComponent: () => import('./features/wallet/wallet.component').then(m => m.WalletComponent)
  },
  {
    path: 'trade',
    redirectTo: '/trade/BTC-USD',
    pathMatch: 'full'
  },
  {
    path: 'trade/:symbol',
    canActivate: [authGuard],
    loadComponent: () => import('./features/trading/trading-page.component').then(m => m.TradingPageComponent)
  },
  {
    path: 'simulator',
    canActivate: [authGuard],
    loadComponent: () => import('./features/simulator/simulator-page.component').then(m => m.SimulatorPageComponent)
  },
  // Profile route
  {
    path: 'profile',
    canActivate: [authGuard],
    loadComponent: () => import('./features/profile/profile.component').then(m => m.ProfileComponent)
  },
  // Admin route
  {
    path: 'admin',
    canActivate: [adminGuard],
    loadComponent: () => import('./features/admin/admin.component').then(m => m.AdminComponent)
  },
  // Disputes route
  {
    path: 'disputes',
    canActivate: [authGuard],
    loadComponent: () => import('./features/disputes/disputes.component').then(m => m.DisputesComponent)
  },
  // Forum routes
  {
    path: 'forum',
    canActivate: [authGuard],
    loadComponent: () => import('./features/forum/forum.component').then(m => m.ForumComponent)
  },
  {
    path: 'forum/category/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./features/forum/category-posts/category-posts.component').then(m => m.CategoryPostsComponent)
  },
  {
    path: 'forum/post/create/:categoryId',
    canActivate: [authGuard],
    loadComponent: () => import('./features/forum/post-form/post-form.component').then(m => m.PostFormComponent)
  },
  {
    path: 'forum/post/edit/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./features/forum/post-form/post-form.component').then(m => m.PostFormComponent)
  },
  {
    path: 'forum/post/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./features/forum/post-detail/post-detail.component').then(m => m.PostDetailComponent)
  },
  // Formations route
  {
    path: 'formations',
    canActivate: [authGuard],
    loadComponent: () => import('./features/formations/formation-ai.component').then(m => m.FormationAIComponent)
  },
  // Course Generator route (Admin only)
  {
    path: 'formations/generate',
    canActivate: [authGuard],
    loadComponent: () => import('./features/formations/course-generator.component').then(m => m.CourseGeneratorComponent)
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];
