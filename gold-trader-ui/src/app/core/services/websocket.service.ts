import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { EMPTY, Observable, Subject, BehaviorSubject, timer, throwError, of } from 'rxjs';
import { catchError, delay, distinctUntilChanged, filter, retry, switchMap, takeUntil, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

import { PriceTick, TradingSignal, TradeUpdate, AccountUpdate } from '@core/models/trading.models';
import { AuthService } from './auth.service';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: any;
}

export interface WebSocketResponse {
  type: string;
  data: any;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket$!: WebSocketSubject<WebSocketResponse>;
  private readonly reconnectInterval = environment.wsReconnectInterval;
  private readonly maxReconnectAttempts = environment.wsMaxReconnectAttempts;
  private reconnectAttempts = 0;
  private connectionStatus$ = new BehaviorSubject<boolean>(false);
  private destroy$ = new Subject<void>();
  private offlineQueue: any[] = [];
  private isReconnecting = false;

  // Observable streams for different data types
  private priceFeed$ = new Subject<PriceTick>();
  private signals$ = new Subject<TradingSignal>();
  private trades$ = new Subject<TradeUpdate>();
  private account$ = new Subject<AccountUpdate>();
  private connectionErrors$ = new Subject<any>();
  private queueProcessed$ = new Subject<void>();
  
  // Public observable streams
  public priceFeed = this.priceFeed$.asObservable();
  public signals = this.signals$.asObservable();
  public trades = this.trades$.asObservable();
  public account = this.account$.asObservable();
  public connectionErrors = this.connectionErrors$.asObservable();
  public queueProcessed = this.queueProcessed$.asObservable();
  
  constructor(private authService: AuthService) {
    this.authService.authStatus$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(status => {
      if (status === 'AUTHENTICATED') {
        this.connect();
      } else {
        this.disconnect();
      }
    });
  }
  
  private connect(): void {
    if (!this.socket$ || this.socket$.closed) {
      this.socket$ = this.createWebSocket();
      this.setupMessageHandling();
      this.setupConnectionMonitoring();
    }
  }
  
  disconnect(): void {
    this.destroy$.next();
    this.offlineQueue = [];
    if (this.socket$) {
      this.socket$.complete();
    }
  }
  
  private createWebSocket(): WebSocketSubject<WebSocketResponse> {
    const token = this.authService.getToken();
    if (!token) {
      console.error('Cannot connect to WebSocket: No authentication token');
      return throwError('No authentication token') as any;
    }
    
    const wsUrl = `${environment.wsUrl}?token=${token}`;
    
    return webSocket({
      url: wsUrl,
      openObserver: {
        next: () => this.handleOpen()
      },
      closeObserver: {
        next: () => this.handleClose()
      }
    });
  }
  
  private setupMessageHandling(): void {
    this.socket$.pipe(
      takeUntil(this.destroy$),
      retry({
        delay: this.reconnectInterval,
        count: this.maxReconnectAttempts
      }),
      catchError((error: any) => {
        this.handleError(error);
        return EMPTY;
      })
    ).subscribe({
      next: (message) => this.handleMessage(message)
    });
  }
  
  private setupConnectionMonitoring(): void {
    // Heartbeat mechanism to detect connection issues
    this.socket$.pipe(
      takeUntil(this.destroy$),
      filter(message => message.type === 'heartbeat')
    ).subscribe(() => {
      // Reset reconnect attempts on successful heartbeat
      this.reconnectAttempts = 0;
    });
    
    // Send periodic heartbeat
    timer(0, 30000).pipe(
      takeUntil(this.destroy$),
      switchMap(() => this.sendMessage({ type: 'heartbeat' }))
    ).subscribe();
  }
  
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.connectionStatus$.next(true);
    this.reconnectAttempts = 0;
    this.isReconnecting = false;

    // Process any queued messages first
    this.processOfflineQueue();

    // Subscribe to data channels
    this.subscribeToChannels();
  }
  
  private handleClose(): void {
    console.log('WebSocket disconnected');
    this.connectionStatus$.next(false);
    this.isReconnecting = true;

    // Attempt reconnection if not intentionally disconnected
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);

      timer(this.reconnectInterval).pipe(
        takeUntil(this.destroy$)
      ).subscribe(() => {
        this.connect();
      });
    } else {
      console.error('Max reconnection attempts reached');
      this.connectionErrors$.next({
        type: 'MAX_RECONNECT_ATTEMPTS',
        message: 'Failed to reconnect after maximum attempts'
      });
    }
  }
  
  private handleError(error: any): void {
    console.error('WebSocket error:', error);
    this.connectionErrors$.next({
      type: 'CONNECTION_ERROR',
      message: error.message || 'Unknown WebSocket error',
      details: error
    });
  }
  
  private handleMessage(message: WebSocketResponse): void {
    if (!message || !message.type) {
      return;
    }
    
    switch (message.type) {
      case 'price_tick':
        this.priceFeed$.next(message.data);
        break;
        
      case 'signal_created':
      case 'signal_updated':
        this.signals$.next(message.data);
        break;
        
      case 'trade_created':
      case 'trade_updated':
      case 'trade_closed':
        this.trades$.next(message.data);
        break;
        
      case 'account_update':
        this.account$.next(message.data);
        break;
        
      case 'subscription_result':
        console.log('Subscription result:', message.data);
        break;
        
      case 'error':
        this.connectionErrors$.next({
          type: 'SERVER_ERROR',
          message: message.data.message || 'Server error',
          details: message.data
        });
        break;
        
      default:
        console.log('Unhandled WebSocket message type:', message.type, message.data);
    }
  }
  
  private subscribeToChannels(): void {
    // Subscribe to all relevant channels
    const subscriptions = [
      { type: 'subscribe', channel: 'price_feed', instrument: 'XAUUSD' },
      { type: 'subscribe', channel: 'signals' },
      { type: 'subscribe', channel: 'trades' },
      { type: 'subscribe', channel: 'account' }
    ];
    
    subscriptions.forEach(sub => this.sendMessage(sub));
  }
  
  sendMessage(message: any): Observable<any> {
    if (!this.socket$ || this.socket$.closed || this.isReconnecting) {
      console.warn('WebSocket not connected, queuing message');
      this.offlineQueue.push(message);
      return of({ success: false, queued: true });
    }

    try {
      this.socket$.next(message);
      return new Observable(observer => {
        observer.next({ success: true });
        observer.complete();
      });
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return throwError(error);
    }
  }

  private processOfflineQueue(): void {
    if (this.offlineQueue.length === 0) {
      this.queueProcessed$.next();
      return;
    }

    console.log(`Processing ${this.offlineQueue.length} queued messages`);

    // Process each queued message
    this.offlineQueue.forEach(message => {
      try {
        if (this.socket$ && !this.socket$.closed) {
          this.socket$.next(message);
        }
      } catch (error) {
        console.error('Error processing queued message:', error);
      }
    });

    // Clear the queue after processing
    this.offlineQueue = [];
    this.queueProcessed$.next();
  }
  
  // Channel-specific subscription methods
  subscribeToPriceFeed(instrument: string = 'XAUUSD'): Observable<any> {
    return this.sendMessage({
      type: 'subscribe',
      channel: 'price_feed',
      instrument
    });
  }
  
  subscribeToSignals(): Observable<any> {
    return this.sendMessage({
      type: 'subscribe',
      channel: 'signals'
    });
  }
  
  subscribeToTrades(): Observable<any> {
    return this.sendMessage({
      type: 'subscribe',
      channel: 'trades'
    });
  }
  
  subscribeToAccount(): Observable<any> {
    return this.sendMessage({
      type: 'subscribe',
      channel: 'account'
    });
  }
  
  unsubscribeFromChannel(channel: string, instrument?: string): Observable<any> {
    const message: any = {
      type: 'unsubscribe',
      channel
    };
    
    if (instrument) {
      message.instrument = instrument;
    }
    
    return this.sendMessage(message);
  }
  
  getConnectionStatus(): Observable<boolean> {
    return this.connectionStatus$.asObservable();
  }

  isConnected(): boolean {
    return this.socket$ && !this.socket$.closed && !this.isReconnecting;
  }

  getQueueLength(): number {
    return this.offlineQueue.length;
  }
}