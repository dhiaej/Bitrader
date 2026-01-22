import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // First check if user is authenticated
  if (!authService.isAuthenticated()) {
    router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }

  // Then check if user is admin
  const currentUser = authService.getCurrentUser();
  if (!currentUser || !currentUser.is_admin) {
    router.navigate(['/dashboard']);
    return false;
  }

  return true;
};

