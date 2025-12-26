// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Injectable, inject } from '@angular/core';
import { CanActivate, Router, RouterStateSnapshot, ActivatedRouteSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { map, take } from 'rxjs/operators';

import { AuthService, AuthStatus } from '../services/auth.service';
import { Permission, UserRole } from '../models/auth.models';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  private authService = inject(AuthService);
  private router = inject(Router);

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | Promise<boolean> | boolean {
    return this.authService.authStatus$.pipe(
      take(1),
      map((status: AuthStatus) => {
        if (status === AuthStatus.Authenticated) {
          // Check if user has required role
          const requiredRole = route.data['role'] as UserRole;
          const requiredPermissions = route.data['permissions'] as Permission[];
          
          if (requiredRole && !this.authService.hasRole(requiredRole)) {
            this.router.navigate(['/unauthorized']);
            return false;
          }
          
          if (requiredPermissions && !this.authService.hasAnyPermission(requiredPermissions)) {
            this.router.navigate(['/unauthorized']);
            return false;
          }
          
          return true;
        } else {
          // Not authenticated, redirect to login
          this.router.navigate(['/login'], {
            queryParams: { returnUrl: state.url }
          });
          return false;
        }
      })
    );
  }
}