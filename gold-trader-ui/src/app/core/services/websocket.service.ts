// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Injectable, OnDestroy, inject } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { EMPTY, Subject, BehaviorSubject, timer } from 'rxjs';
import { catchError, retry, takeUntil } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

import { PriceTick, TradingSignal, TradeUpdate, AccountUpdate } from '@core/models/trading.models';
import { AuthService, AuthStatus } from './auth.service';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: unknown;
}

export interface WebSocketResponse {
  type: string;
  data: unknown;
  timestamp: string;
}

export enum ConnectionStatus {
  Connecting = 'Connecting',
  Connected = 'Connected',
  Reconnecting = 'Reconnecting',
  Disconnected = 'Disconnected',
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService implements OnDestroy {
  private socket$!: WebSocketSubject<WebSocketResponse>;
  private readonly reconnectInterval = environment.wsReconnectInterval;
  private readonly maxReconnectAttempts = environment.wsMaxReconnectAttempts;
  private connectionStatusSubject = new BehaviorSubject<ConnectionStatus>(ConnectionStatus.Disconnected);
  private destroy$ = new Subject<void>();
  private offlineQueue: WebSocketMessage[] = [];

  private authService = inject(AuthService);

  // Observable streams for different data types
  private priceFeed$ = new Subject<PriceTick>();
  private signals$ = new Subject<TradingSignal>();
  private trades$ = new Subject<TradeUpdate>();
  private account$ = new Subject<AccountUpdate>();
  private connectionErrors$ = new Subject<Event>();
  
  // Public observable streams
  public connectionStatus$ = this.connectionStatusSubject.asObservable();
  public priceFeed = this.priceFeed$.asObservable();
  public signals = this.signals$.asObservable();
  public trades = this.trades$.asObservable();
  public account = this.account$.asObservable();
  public connectionErrors = this.connectionErrors$.asObservable();
  
  constructor() {
    this.authService.authStatus$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(status => {
      if (status === AuthStatus.Authenticated) {
        this.connect();
      } else {
        this.disconnect();
      }
    });
  }
  
  ngOnDestroy(): void {
    this.disconnect();
    this.destroy$.complete();
  }

  private connect(): void {
    if (this.socket$ && !this.socket$.closed) {
      return;
    }
    
    this.connectionStatusSubject.next(ConnectionStatus.Connecting);
    
    try {
      this.socket$ = this.createWebSocket();
      this.setupMessageHandling();
    } catch (error) {
      this.handleError(error as Error);
      this.connectionStatusSubject.next(ConnectionStatus.Disconnected);
    }
  }
  
  disconnect(): void {
    if (this.socket$) {
      this.socket$.complete();
    }
    this.connectionStatusSubject.next(ConnectionStatus.Disconnected);
    this.offlineQueue = [];
    this.destroy$.next();
  }
  
  private createWebSocket(): WebSocketSubject<WebSocketResponse> {
    const token = this.authService.getToken();
    if (!token) {
      throw new Error('Cannot connect to WebSocket: No authentication token');
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
        count: this.maxReconnectAttempts,
        delay: (error, retryCount) => {
          this.connectionStatusSubject.next(ConnectionStatus.Reconnecting);
          console.log(`Attempting to reconnect... (${retryCount}/${this.maxReconnectAttempts})`);
          return timer(this.reconnectInterval);
        }
      }),
      catchError((error: Event) => {
        this.handleError(error);
        this.connectionStatusSubject.next(ConnectionStatus.Disconnected);
        return EMPTY;
      })
    ).subscribe({
      next: (message) => this.handleMessage(message)
    });
  }
  
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.connectionStatusSubject.next(ConnectionStatus.Connected);
    this.processOfflineQueue();
    this.subscribeToChannels();
  }
  
  private handleClose(): void {
    // This is handled by the retry operator's delay function now
    console.log('WebSocket connection closed');
  }
  
  private handleError(error: Event | Error): void {
    console.error('WebSocket error:', error);
    if (error instanceof Event) {
        this.connectionErrors$.next(error);
    } else {
        // Create a synthetic error event
        this.connectionErrors$.next(new ErrorEvent('error', { error }));
    }
  }
  
  private handleMessage(message: WebSocketResponse): void {
    if (!message || !message.type) {
      return;
    }
    
    switch (message.type) {
      case 'price_tick':
        this.priceFeed$.next(message.data as PriceTick);
        break;
      case 'signal_created':
      case 'signal_updated':
        this.signals$.next(message.data as TradingSignal);
        break;
      case 'trade_created':
      case 'trade_updated':
      case 'trade_closed':
        this.trades$.next(message.data as TradeUpdate);
        break;
      case 'account_update':
        this.account$.next(message.data as AccountUpdate);
        break;
      case 'subscription_result':
        console.log('Subscription result:', message.data);
        break;
      case 'error':
        this.connectionErrors$.next(new ErrorEvent('error', { message: (message.data as any)?.message || 'Server error', error: message.data }));
        break;
      case 'heartbeat':
        // Heartbeat received, connection is alive
        break;
      default:
        console.warn('Unhandled WebSocket message type:', message.type, message.data);
    }
  }
  
  private subscribeToChannels(): void {
    const subscriptions: WebSocketMessage[] = [
      { type: 'subscribe', timestamp: new Date().toISOString(), data: { channel: 'price_feed', instrument: 'XAUUSD' } },
      { type: 'subscribe', timestamp: new Date().toISOString(), data: { channel: 'signals' } },
      { type: 'subscribe', timestamp: new Date().toISOString(), data: { channel: 'trades' } },
      { type: 'subscribe', timestamp: new Date().toISOString(), data: { channel: 'account' } }
    ];
    
    subscriptions.forEach(sub => this.sendMessage(sub));
  }
  
  sendMessage(message: WebSocketMessage): void {
    if (this.connectionStatusSubject.value !== ConnectionStatus.Connected) {
      console.warn('WebSocket not connected, queuing message:', message);
      this.offlineQueue.push(message);
      return;
    }

    try {
      this.socket$.next(message as WebSocketResponse);
    } catch (error) {
      this.handleError(error as Error);
    }
  }

  private processOfflineQueue(): void {
    if (this.offlineQueue.length === 0) {
      return;
    }

    console.log(`Processing ${this.offlineQueue.length} queued messages`);
    
    while (this.offlineQueue.length > 0) {
      const message = this.offlineQueue.shift();
      if (message) {
        this.sendMessage(message);
      }
    }
  }
  
  // Public methods for components to subscribe/unsubscribe
  subscribeToPriceFeed(instrument: string = 'XAUUSD'): void {
    this.sendMessage({
      type: 'subscribe',
      timestamp: new Date().toISOString(),
      data: { channel: 'price_feed', instrument }
    });
  }
  
  unsubscribeFromPriceFeed(instrument: string = 'XAUUSD'): void {
    this.sendMessage({
      type: 'unsubscribe',
      timestamp: new Date().toISOString(),
      data: { channel: 'price_feed', instrument }
    });
  }
}