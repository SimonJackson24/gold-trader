import { Injectable } from '@angular/core';
import { CanActivate, Router, RouterStateSnapshot, ActivatedRouteSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { map, take } from 'rxjs/operators';

import { AuthService, AuthStatus } from '../services/auth.service';
import { UserRole } from '../models/auth.models';

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}
  
  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | Promise<boolean> | boolean {
    const requiredRole = route.data['role'] as UserRole;
    
    return this.authService.authStatus$.pipe(
      take(1),
      map(status => {
        if (status === AuthStatus.Authenticated) {
          if (requiredRole && this.authService.hasRole(requiredRole)) {
            return true;
          } else {
            this.router.navigate(['/unauthorized']);
            return false;
          }
        } else {
          this.router.navigate(['/login'], {
            queryParams: { returnUrl: state.url }
          });
          return false;
        }
      })
    );
  }
}