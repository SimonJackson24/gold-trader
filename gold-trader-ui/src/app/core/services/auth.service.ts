// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Injectable, OnDestroy, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError, timer, Subject, Subscription } from 'rxjs';
import { catchError, tap, takeUntil, switchMap } from 'rxjs/operators';
import { JwtHelperService } from '@auth0/angular-jwt';
import { Router } from '@angular/router';

import { environment } from '../../../environments/environment';
import {
  LoginCredentials,
  AuthResponse,
  User,
  TokenPayload,
  RefreshTokenRequest,
  ChangePasswordRequest,
  AuthStatus,
  Permission,
  UserRole
} from '@core/models/auth.models';

// Re-export AuthStatus for use in guards
export { AuthStatus } from '@core/models/auth.models';

@Injectable({
  providedIn: 'root'
})
export class AuthService implements OnDestroy {
  private readonly API_URL = environment.apiUrl;
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'current_user';

  private http = inject(HttpClient);
  private jwtHelper = inject(JwtHelperService);
  private router = inject(Router);

  private authStatusSubject = new BehaviorSubject<AuthStatus>(AuthStatus.NotAuthenticated);
  private currentUserSubject = new BehaviorSubject<User | null>(null);

  public authStatus$ = this.authStatusSubject.asObservable();
  public currentUser$ = this.currentUserSubject.asObservable();

  private refreshTimer$ = new Subject<void>();
  private destroy$ = new Subject<void>();
  private refreshSubscription: Subscription | null = null;

  constructor() {
    this.initializeAuthFromStorage();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.refreshTimer$.next();
    this.refreshTimer$.complete();
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  private initializeAuthFromStorage(): void {
    const token = this.getToken();
    if (!token) {
      this.authStatusSubject.next(AuthStatus.NotAuthenticated);
      return;
    }

    const user = this.getUser();

    if (!this.jwtHelper.isTokenExpired(token)) {
      this.currentUserSubject.next(user);
      this.authStatusSubject.next(AuthStatus.Authenticated);
      this.scheduleTokenRefresh();
    } else {
      this.authStatusSubject.next(AuthStatus.TokenExpired);
      this.refreshToken().subscribe({
        error: () => this.logout() // If refresh fails, log out
      });
    }
  }

  login(credentials: LoginCredentials): Observable<AuthResponse> {
    this.authStatusSubject.next(AuthStatus.Initializing);

    return this.http.post<AuthResponse>(`${this.API_URL}/auth/login`, credentials)
      .pipe(
        tap(response => {
          this.storeTokens(response);
          this.storeUser(response.user);
          this.currentUserSubject.next(response.user);
          this.authStatusSubject.next(AuthStatus.Authenticated);
          this.scheduleTokenRefresh();
        }),
        catchError(error => {
          this.authStatusSubject.next(AuthStatus.Error);
          return this.handleAuthError(error);
        })
      );
  }

  logout(redirectToLogin: boolean = true): void {
    // Stop the refresh timer
    this.refreshTimer$.next();

    // Call backend logout endpoint to invalidate token first
    this.http.post(`${this.API_URL}/auth/logout`, {}).subscribe({
        next: () => this.finalizeLogout(redirectToLogin),
        error: () => this.finalizeLogout(redirectToLogin) // Finalize logout even if server call fails
    });
  }
  
  private finalizeLogout(redirectToLogin: boolean): void {
    this.clearTokens();
    this.clearUser();
    this.currentUserSubject.next(null);
    this.authStatusSubject.next(AuthStatus.NotAuthenticated);

    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
      this.refreshSubscription = null;
    }

    if (redirectToLogin) {
      this.router.navigate(['/auth/login']);
    }
  }

  refreshToken(): Observable<AuthResponse> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.logout();
      return throwError(() => new Error('No refresh token available'));
    }

    this.authStatusSubject.next(AuthStatus.Refreshing);

    const request: RefreshTokenRequest = { refresh_token: refreshToken };

    return this.http.post<AuthResponse>(`${this.API_URL}/auth/refresh`, request)
      .pipe(
        tap(response => {
          this.storeTokens(response);
          // The refresh response might not contain the full user object.
          // Let's keep the existing user data if the response doesn't have it.
          if (response.user) {
            this.storeUser(response.user);
            this.currentUserSubject.next(response.user);
          }
          this.authStatusSubject.next(AuthStatus.Authenticated);
          this.scheduleTokenRefresh();
        }),
        catchError(error => {
          // On refresh error, we must log out
          this.logout();
          return this.handleAuthError(error);
        })
      );
  }

  changePassword(request: ChangePasswordRequest): Observable<void> {
    return this.http.post<void>(`${this.API_URL}/auth/change-password`, request)
      .pipe(catchError(error => this.handleAuthError(error)));
  }

  forgotPassword(email: string): Observable<void> {
    return this.http.post<void>(`${this.API_URL}/auth/forgot-password`, { email })
      .pipe(catchError(error => this.handleAuthError(error)));
  }

  resetPassword(token: string, newPassword: string, confirmPassword: string): Observable<void> {
    return this.http.post<void>(`${this.API_URL}/auth/reset-password`, {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword
    }).pipe(catchError(error => this.handleAuthError(error)));
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  getUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    return token !== null && !this.jwtHelper.isTokenExpired(token);
  }

  hasRole(role: UserRole): boolean {
    const user = this.currentUserSubject.value;
    return user ? user.role === role : false;
  }

  hasPermission(permission: Permission): boolean {
    const user = this.currentUserSubject.value;
    return user ? (user.permissions || []).includes(permission) : false;
  }

  hasAnyPermission(permissions: Permission[]): boolean {
    const user = this.currentUserSubject.value;
    return user ? permissions.some(p => (user.permissions || []).includes(p)) : false;
  }

  getTokenPayload(): TokenPayload | null {
    const token = this.getToken();
    return token ? this.jwtHelper.decodeToken(token) : null;
  }

  private storeTokens(response: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.access_token);
    if (response.refresh_token) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refresh_token);
    }
  }

  private storeUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  private clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  private clearUser(): void {
    localStorage.removeItem(this.USER_KEY);
  }

  private scheduleTokenRefresh(): void {
    // Cancel any previous timer
    this.refreshTimer$.next();
    
    const token = this.getToken();
    if (!token) return;

    const expiresAt = this.jwtHelper.getTokenExpirationDate(token)?.getTime();
    if (!expiresAt) return;

    // Refresh the token `tokenRefreshThreshold` milliseconds before it expires
    const refreshAt = expiresAt - Date.now() - environment.tokenRefreshThreshold;
    
    if (refreshAt <= 0) {
      this.refreshToken().subscribe({
        error: () => this.logout()
      });
      return;
    }
    
    this.refreshSubscription = timer(refreshAt).pipe(
      switchMap(() => this.refreshToken()),
      takeUntil(this.refreshTimer$),
      takeUntil(this.destroy$)
    ).subscribe({
      error: () => this.logout()
    });
  }

  private handleAuthError(error: HttpErrorResponse): Observable<never> {
    console.error('Auth error:', error.message || error);
    
    if (error.status === 401) {
      // Don't call logout here as it might cause loops.
      // The refreshToken and initialize methods already handle this.
    }
    
    return throwError(() => error);
  }
}