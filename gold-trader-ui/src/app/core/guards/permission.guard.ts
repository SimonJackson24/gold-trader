import { Injectable } from '@angular/core';
import { CanActivate, Router, RouterStateSnapshot, ActivatedRouteSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { map, take } from 'rxjs/operators';

import { AuthService, AuthStatus } from '../services/auth.service';
import { Permission } from '../models/auth.models';

@Injectable({
  providedIn: 'root'
})
export class PermissionGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}
  
  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | Promise<boolean> | boolean {
    const requiredPermissions = route.data['permissions'] as Permission[];
    
    return this.authService.authStatus$.pipe(
      take(1),
      map((status: AuthStatus) => {
        if (status === AuthStatus.Authenticated) {
          if (requiredPermissions && this.authService.hasAnyPermission(requiredPermissions)) {
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