import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError, timer, Subject, EMPTY } from 'rxjs';
import { catchError, map, tap, switchMap, takeUntil, filter } from 'rxjs/operators';
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
export class AuthService {
  private readonly API_URL = environment.apiUrl;
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'current_user';
  
  private authStatusSubject = new BehaviorSubject<AuthStatus>(AuthStatus.NotAuthenticated);
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  
  public authStatus$ = this.authStatusSubject.asObservable();
  public currentUser$ = this.currentUserSubject.asObservable();
  
  private refreshTimer: any;
  private destroy$ = new Subject<void>();
  private refreshSubscription: any = null;
  
  constructor(
    private http: HttpClient,
    private jwtHelper: JwtHelperService,
    private router: Router
  ) {
    this.initializeAuthFromStorage();
    this.setupTokenRefresh();
  }
  
  private initializeAuthFromStorage(): void {
    const token = this.getToken();
    const user = this.getUser();

    if (token && !this.jwtHelper.isTokenExpired(token)) {
      this.currentUserSubject.next(user);
      this.authStatusSubject.next(AuthStatus.Authenticated);
      this.scheduleTokenRefresh();
    } else if (token && this.jwtHelper.isTokenExpired(token)) {
      this.authStatusSubject.next(AuthStatus.TokenExpired);
      this.refreshToken().subscribe();
    } else {
      this.authStatusSubject.next(AuthStatus.NotAuthenticated);
    }
  }

  private setupTokenRefresh(): void {
    // Start token refresh timer when authenticated
    this.authStatus$.pipe(
      takeUntil(this.destroy$),
      filter(status => status === AuthStatus.Authenticated)
    ).subscribe(() => {
      if (!this.refreshSubscription) {
        this.refreshSubscription = timer(environment.tokenRefreshThreshold, environment.tokenRefreshThreshold).pipe(
          takeUntil(this.destroy$),
          switchMap(() => this.refreshToken())
        ).subscribe();
      }
    });
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
    this.clearTokens();
    this.clearUser();
    this.currentUserSubject.next(null);
    this.authStatusSubject.next(AuthStatus.NotAuthenticated);

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
      this.refreshSubscription = null;
    }

    // Call backend logout endpoint to invalidate token
    this.http.post(`${this.API_URL}/auth/logout`, {}).subscribe();

    if (redirectToLogin) {
      this.router.navigate(['/login']);
    }
  }
  
  refreshToken(): Observable<AuthResponse> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.logout();
      return throwError('No refresh token available');
    }
    
    this.authStatusSubject.next(AuthStatus.Refreshing);
    
    const request: RefreshTokenRequest = { refresh_token: refreshToken };
    
    return this.http.post<AuthResponse>(`${this.API_URL}/auth/refresh`, request)
      .pipe(
        tap(response => {
          this.storeTokens(response);
          this.currentUserSubject.next(response.user);
          this.authStatusSubject.next(AuthStatus.Authenticated);
          this.scheduleTokenRefresh();
        }),
        catchError(error => {
          this.logout();
          return this.handleAuthError(error);
        })
      );
  }
  
  changePassword(request: ChangePasswordRequest): Observable<any> {
    const headers = this.getAuthHeaders();
    return this.http.post(`${this.API_URL}/auth/change-password`, request, { headers })
      .pipe(catchError(error => this.handleAuthError(error)));
  }
  
  forgotPassword(email: string): Observable<any> {
    return this.http.post(`${this.API_URL}/auth/forgot-password`, { email })
      .pipe(catchError(error => this.handleAuthError(error)));
  }
  
  resetPassword(token: string, newPassword: string, confirmPassword: string): Observable<any> {
    return this.http.post(`${this.API_URL}/auth/reset-password`, {
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
    const user = this.getUser();
    return user ? user.role === role : false;
  }
  
  hasPermission(permission: Permission): boolean {
    const user = this.getUser();
    return user ? user.permissions.includes(permission) : false;
  }
  
  hasAnyPermission(permissions: Permission[]): boolean {
    const user = this.getUser();
    return user ? permissions.some(permission => user.permissions.includes(permission)) : false;
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
  
  private getAuthHeaders(): HttpHeaders {
    const token = this.getToken();
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }
  
  private scheduleTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    
    const token = this.getToken();
    if (token) {
      const expiration = this.jwtHelper.getTokenExpirationDate(token);
      if (expiration) {
        const refreshTime = expiration.getTime() - Date.now() - environment.tokenRefreshThreshold;
        this.refreshTimer = setTimeout(() => {
          this.refreshToken().subscribe();
        }, Math.max(0, refreshTime));
      }
    }
  }
  
  private handleAuthError(error: any): Observable<never> {
    console.error('Auth error:', error);
    console.error(`Status: ${error.status}, Message: ${error.message}, URL: ${error.url}`);
    console.error('Error Body:', error.error);
    
    if (error.status === 401) {
      this.logout();
    }
    
    return throwError(() => error);
  }
}