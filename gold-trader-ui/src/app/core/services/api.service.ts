// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Injectable, inject, OnDestroy } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError, Subject } from 'rxjs';
import { catchError, map, timeout, retryWhen, delay, takeUntil, tap } from 'rxjs/operators';

import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';

import {
  TradingSignal,
  Trade,
  AccountInfo,
  Position,
  PerformanceMetrics,
  SignalQueryParams,
  TradeQueryParams
} from '@core/models/trading.models';

@Injectable({
  providedIn: 'root'
})
export class ApiService implements OnDestroy {
  private readonly API_URL = environment.apiUrl;
  private readonly DEFAULT_TIMEOUT = 30000; // 30 seconds
  private readonly MAX_RETRIES = 3;
  private readonly RETRY_DELAY = 1000;
  private readonly RATE_LIMIT_WINDOW = 60000; // 1 minute
  private readonly MAX_REQUESTS_PER_WINDOW = 60;

  private http = inject(HttpClient);
  private authService = inject(AuthService);

  private requestCounts: {[key: string]: {count: number, timestamp: number}} = {};
  private rateLimitSubject = new Subject<string>();
  private destroy$ = new Subject<void>();
  
  constructor() {}
  
  // Authentication endpoints
  login(credentials: any): Observable<any> {
    return this.http.post(`${this.API_URL}/auth/login`, credentials)
      .pipe(
        timeout(this.DEFAULT_TIMEOUT),
        catchError(error => this.handleError(error))
      );
  }
  
  logout(): Observable<any> {
    return this.http.post(`${this.API_URL}/auth/logout`, {})
      .pipe(
        timeout(this.DEFAULT_TIMEOUT),
        catchError(error => this.handleError(error))
      );
  }
  
  // Signal endpoints
  getSignals(params?: SignalQueryParams): Observable<SignalResponse> {
    const httpParams = this.buildHttpParams(params);
    const headers = this.getAuthHeaders();
    
    return this.http.get<SignalResponse>(`${this.API_URL}/signals`, {
      params: httpParams,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      map(response => this.transformSignalResponse(response)),
      catchError(error => this.handleError(error))
    );
  }
  
  getSignal(signalId: string): Observable<TradingSignal> {
    const headers = this.getAuthHeaders();
    
    return this.http.get<TradingSignal>(`${this.API_URL}/signals/${signalId}`, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  createSignal(signal: Partial<TradingSignal>): Observable<any> {
    const headers = this.getAuthHeaders();
    
    return this.http.post(`${this.API_URL}/signals`, signal, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // Trade endpoints
  getTrades(params?: TradeQueryParams): Observable<TradeResponse> {
    const httpParams = this.buildHttpParams(params);
    const headers = this.getAuthHeaders();
    
    return this.http.get<TradeResponse>(`${this.API_URL}/trades`, {
      params: httpParams,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      map(response => this.transformTradeResponse(response)),
      catchError(error => this.handleError(error))
    );
  }
  
  getTrade(tradeId: string): Observable<Trade> {
    const headers = this.getAuthHeaders();
    
    return this.http.get<Trade>(`${this.API_URL}/trades/${tradeId}`, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  createTrade(trade: Partial<Trade>): Observable<any> {
    const headers = this.getAuthHeaders();
    
    return this.http.post(`${this.API_URL}/trades`, trade, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  closeTrade(tradeId: string, reason: string, percentage: number = 100): Observable<any> {
    const headers = this.getAuthHeaders();
    const body = { reason, percentage };
    
    return this.http.post(`${this.API_URL}/trades/${tradeId}/close`, body, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // Market data endpoints
  getTicks(symbol: string = 'XAUUSD', limit: number = 100): Observable<any> {
    const headers = this.getAuthHeaders();
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('limit', limit.toString());
    
    return this.http.get(`${this.API_URL}/market/ticks`, {
      params,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  getCandles(symbol: string = 'XAUUSD', timeframe: string = 'M15', limit: number = 100): Observable<any> {
    const headers = this.getAuthHeaders();
    const params = new HttpParams()
      .set('symbol', symbol)
      .set('timeframe', timeframe)
      .set('limit', limit.toString());

    return this.http.get(`${this.API_URL}/market/candles`, {
      params,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }

  request<T>(method: string, endpoint: string, data?: any, headers?: HttpHeaders): Observable<T> {
    const url = `${this.API_URL}${endpoint}`;

    switch (method.toUpperCase()) {
      case 'GET':
        return this.http.get<T>(url, { headers });
      case 'POST':
        return this.http.post<T>(url, data, { headers });
      case 'PUT':
        return this.http.put<T>(url, data, { headers });
      case 'DELETE':
        return this.http.delete<T>(url, { headers });
      default:
        throw new Error(`Unsupported HTTP method: ${method}`);
    }
  }
  
  // Account endpoints
  getBalance(): Observable<AccountInfo> {
    const headers = this.getAuthHeaders();
    
    return this.http.get<AccountInfo>(`${this.API_URL}/account/balance`, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  getPositions(): Observable<Position[]> {
    const headers = this.getAuthHeaders();
    
    return this.http.get<Position[]>(`${this.API_URL}/account/positions`, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  getPerformance(params?: any): Observable<PerformanceMetrics> {
    const httpParams = this.buildHttpParams(params);
    const headers = this.getAuthHeaders();
    
    return this.http.get<PerformanceMetrics>(`${this.API_URL}/performance`, {
      params: httpParams,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // Performance endpoints
  getDailyPerformance(params?: any): Observable<PerformanceResponse> {
    const httpParams = this.buildHttpParams(params);
    const headers = this.getAuthHeaders();
    
    return this.http.get<PerformanceResponse>(`${this.API_URL}/performance/daily`, {
      params: httpParams,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  getWeeklyPerformance(params?: any): Observable<PerformanceResponse> {
    const httpParams = this.buildHttpParams(params);
    const headers = this.getAuthHeaders();
    
    return this.http.get<PerformanceResponse>(`${this.API_URL}/performance/weekly`, {
      params: httpParams,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  getMonthlyPerformance(params?: any): Observable<PerformanceResponse> {
    const httpParams = this.buildHttpParams(params);
    const headers = this.getAuthHeaders();
    
    return this.http.get<PerformanceResponse>(`${this.API_URL}/performance/monthly`, {
      params: httpParams,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // Analysis endpoints
  analyzeSmartMoney(symbol: string = 'XAUUSD'): Observable<any> {
    const headers = this.getAuthHeaders();
    const params = new HttpParams().set('symbol', symbol);
    
    return this.http.post(`${this.API_URL}/analysis/smart-money`, {}, {
      params,
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // Configuration endpoints
  getConfig(): Observable<any> {
    const headers = this.getAuthHeaders();
    
    return this.http.get(`${this.API_URL}/config`, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  updateConfig(config: any): Observable<any> {
    const headers = this.getAuthHeaders();
    
    return this.http.put(`${this.API_URL}/config`, config, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // System endpoints
  getSystemStatus(): Observable<any> {
    const headers = this.getAuthHeaders();
    
    return this.http.get(`${this.API_URL}/system/status`, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // WebSocket subscription endpoint
  subscribeToWebSocket(channels: string[]): Observable<any> {
    const headers = this.getAuthHeaders();
    
    return this.http.post(`${this.API_URL}/websocket/subscribe`, {
      channels
    }, {
      headers
    }).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(error => this.handleError(error))
    );
  }
  
  // Helper methods
  private getAuthHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }
  
  private buildHttpParams(params?: any): HttpParams {
    if (!params) {
      return new HttpParams();
    }
    
    let httpParams = new HttpParams();
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        httpParams = httpParams.set(key, params[key].toString());
      }
    });
    
    return httpParams;
  }
  
  private transformSignalResponse(response: any): SignalResponse {
    // Transform backend response to match frontend interface
    return {
      signals: response.signals || [],
      total: response.total || 0,
      limit: response.limit || 50,
      offset: response.offset || 0
    };
  }
  
  private transformTradeResponse(response: any): TradeResponse {
    // Transform backend response to match frontend interface
    return {
      trades: response.trades || [],
      total: response.total || 0,
      limit: response.limit || 50,
      offset: response.offset || 0
    };
  }
  
  private rateLimitHandler() {
    return (source: Observable<any>) => source.pipe(
      retryWhen(errors => errors.pipe(
        delay(this.RETRY_DELAY),
        takeUntil(this.destroy$),
        tap(error => {
          if (error.status === 429) {
            this.rateLimitSubject.next('Rate limit exceeded. Waiting before retry...');
          }
        })
      ))
    );
  }

  private checkRateLimit(endpoint: string): boolean {
    const now = Date.now();
    const windowStart = now - this.RATE_LIMIT_WINDOW;

    // Reset count if window has passed
    if (this.requestCounts[endpoint] && this.requestCounts[endpoint].timestamp < windowStart) {
      this.requestCounts[endpoint] = { count: 0, timestamp: now };
    }

    // Initialize if not exists
    if (!this.requestCounts[endpoint]) {
      this.requestCounts[endpoint] = { count: 0, timestamp: now };
    }

    // Check if limit reached
    if (this.requestCounts[endpoint].count >= this.MAX_REQUESTS_PER_WINDOW) {
      console.warn(`Rate limit reached for ${endpoint}`);
      this.rateLimitSubject.next(`Rate limit reached for ${endpoint}. Please wait before making more requests.`);
      return false;
    }

    // Increment count
    this.requestCounts[endpoint].count++;
    return true;
  }

  private handleError(error: any): Observable<never> {
    console.error('API Error:', error);
    console.error(`Status: ${error.status}, Message: ${error.message}, URL: ${error.url}`);
    console.error('Error Body:', error.error);

    if (error.status === 401) {
      // Unauthorized - token expired or invalid
      this.authService.logout();
    } else if (error.status === 429) {
      // Rate limit exceeded
      this.rateLimitSubject.next('Rate limit exceeded. Please try again later.');
    }

    return throwError(() => error);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}

// Response interfaces for API calls
export interface SignalResponse {
  signals: TradingSignal[];
  total: number;
  limit: number;
  offset: number;
}

export interface TradeResponse {
  trades: Trade[];
  total: number;
  limit: number;
  offset: number;
}

export interface AccountResponse {
  account: AccountInfo;
}

export interface PerformanceResponse {
  metrics: PerformanceMetrics[];
  summary: {
    total_days: number;
    average_win_rate: number;
    total_profit_loss: number;
    total_pips: number;
  };
}