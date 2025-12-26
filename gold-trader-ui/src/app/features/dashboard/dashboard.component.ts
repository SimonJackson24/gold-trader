// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, inject } from '@angular/core';
import { Observable, Subject, of } from 'rxjs';
import { takeUntil, catchError, map } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { CurrencyPipe, PercentPipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';

import { AccountInfo, TradingSignal, PerformanceMetrics, SignalResponse, PerformanceResponse } from '@core/models/trading.models';
import { ApiService } from '@core/services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    CurrencyPipe,
    PercentPipe
  ],
  template: `
    <div class="dashboard-container" role="region" aria-label="Trading dashboard">
      <div class="dashboard-header">
        <h1>Trading Dashboard</h1>
      </div>

      <div class="dashboard-grid">
        <!-- Account Overview -->
        <mat-card class="dashboard-card" role="region" aria-label="Account overview">
          <mat-card-header>
            <mat-card-title>Account Overview</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="account-info" *ngIf="accountInfo$ | async as accountInfo" role="grid" aria-label="Account information">
              <div class="info-row" role="row">
                <span class="label" role="columnheader">Balance:</span>
                <span class="value" role="gridcell">{{accountInfo.balance | currency}}</span>
              </div>
              <div class="info-row" role="row">
                <span class="label" role="columnheader">Equity:</span>
                <span class="value" role="gridcell">{{accountInfo.equity | currency}}</span>
              </div>
              <div class="info-row" role="row">
                <span class="label" role="columnheader">Profit/Loss:</span>
                <span class="value" role="gridcell" [class.positive]="accountInfo.profit >= 0" [class.negative]="accountInfo.profit < 0">
                  {{accountInfo.profit | currency}}
                </span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Recent Signals -->
        <mat-card class="dashboard-card" role="region" aria-label="Recent trading signals">
          <mat-card-header>
            <mat-card-title>Recent Signals</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="signals-list" *ngIf="recentSignals$ | async as signals" role="list">
              <div class="signal-item" *ngFor="let signal of signals.slice(0, 5); let i = index" role="listitem" [attr.aria-label]="'Signal ' + (i + 1)">
                <div class="signal-direction" [class.buy]="signal.direction === 'BUY'" [class.sell]="signal.direction === 'SELL'" [attr.aria-label]="signal.direction + ' signal'">
                  {{signal.direction}}
                </div>
                <div class="signal-info">
                  <div class="signal-pair">{{signal.instrument}}</div>
                  <div class="signal-price">{{signal.entry_price}}</div>
                </div>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Performance -->
        <mat-card class="dashboard-card" role="region" aria-label="Trading performance">
          <mat-card-header>
            <mat-card-title>Performance</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="performance-metrics" *ngIf="performanceMetrics$ | async as metrics" role="grid" aria-label="Performance metrics">
              <div class="metric" role="row">
                <span class="metric-label" role="columnheader">Win Rate:</span>
                <span class="metric-value" role="gridcell">{{metrics.win_rate | percent}}</span>
              </div>
              <div class="metric" role="row">
                <span class="metric-label" role="columnheader">Total Pips:</span>
                <span class="metric-value" role="gridcell">{{metrics.total_pips}}</span>
              </div>
              <div class="metric" role="row">
                <span class="metric-label" role="columnheader">Profit/Loss:</span>
                <span class="metric-value" role="gridcell" [class.positive]="metrics.total_profit_loss >= 0" [class.negative]="metrics.total_profit_loss < 0">
                  {{metrics.total_profit_loss | currency}}
                </span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styleUrls: ['./dashboard.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private apiService = inject(ApiService);

  accountInfo$!: Observable<AccountInfo>;
  recentSignals$!: Observable<TradingSignal[]>;
  performanceMetrics$!: Observable<PerformanceMetrics>;

  ngOnInit(): void {
    this.loadDashboardData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDashboardData(): void {
    // Load account information with fallback to mock data
    this.accountInfo$ = this.apiService.getBalance().pipe(
      catchError(error => {
        console.error('Error loading account balance:', error);
        return of(this.generateMockAccountInfo());
      }),
      takeUntil(this.destroy$)
    );

    // Load recent signals - transform SignalResponse to TradingSignal[] with error handling
    this.recentSignals$ = this.apiService.getSignals({ limit: 10 }).pipe(
      map((response: SignalResponse) => response.signals),
      catchError((error: any) => {
        console.error('Error loading signals:', error);
        return of(this.generateMockSignals());
      }),
      takeUntil(this.destroy$)
    );

    // Load performance metrics - get the most recent day's metrics or use summary with error handling
    this.performanceMetrics$ = this.apiService.getDailyPerformance().pipe(
      map((response: PerformanceResponse) => {
        // If we have metrics data, use the first (most recent) day
        if (response.metrics && response.metrics.length > 0) {
          return response.metrics[0];
        }
        // Otherwise, create a metrics object from the summary data
        return {
          date: new Date().toISOString().split('T')[0],
          instrument: 'XAUUSD',
          total_signals: 0,
          total_trades: 0,
          winning_trades: 0,
          losing_trades: 0,
          win_rate: response.summary?.average_win_rate || 0,
          average_rr: 0,
          total_pips: response.summary?.total_pips || 0,
          total_profit_loss: response.summary?.total_profit_loss || 0,
          largest_win: 0,
          largest_loss: 0,
          max_drawdown: 0,
          sharpe_ratio: 0
        } as PerformanceMetrics;
      }),
      catchError((error: any) => {
        console.error('Error loading performance metrics:', error);
        return of(this.generateMockPerformanceMetrics());
      }),
      takeUntil(this.destroy$)
    );
  }

  private generateMockAccountInfo(): AccountInfo {
    return {
      balance: 10000,
      equity: 10500,
      margin: 1000,
      margin_free: 9000,
      margin_level: 1050,
      profit: 500,
      open_trades: 2,
      closed_trades: 15,
      total_volume: 28,
      deposit: 10000,
      withdrawal: 0
    };
  }

  private generateMockSignals(): TradingSignal[] {
    return [
      {
        signal_id: '1',
        instrument: 'XAUUSD',
        direction: 'BUY',
        entry_price: 2305.50,
        stop_loss: 2300.00,
        take_profit_1: 2315.00,
        take_profit_2: 2320.00,
        risk_reward_ratio: 2.5,
        position_size: 0.1,
        risk_percentage: 1,
        setup_type: 'FVG',
        market_structure: 'BOS',
        confluence_factors: ['Order Block', 'Liquidity Sweep'],
        confidence_score: 0.85,
        h4_context: 'Uptrend',
        h1_context: 'Pullback',
        m15_context: 'Breakout',
        session: 'LONDON',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'ACTIVE'
      },
      {
        signal_id: '2',
        instrument: 'XAUUSD',
        direction: 'SELL',
        entry_price: 2302.75,
        stop_loss: 2307.00,
        take_profit_1: 2295.00,
        take_profit_2: 2290.00,
        risk_reward_ratio: 2.0,
        position_size: 0.1,
        risk_percentage: 1,
        setup_type: 'Order Block',
        market_structure: 'CHoCH',
        confluence_factors: ['FVG', 'Liquidity Pool'],
        confidence_score: 0.75,
        h4_context: 'Downtrend',
        h1_context: 'Retracement',
        m15_context: 'Rejection',
        session: 'LONDON',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        updated_at: new Date(Date.now() - 3600000).toISOString(),
        status: 'ACTIVE'
      },
      {
        signal_id: '3',
        instrument: 'XAUUSD',
        direction: 'BUY',
        entry_price: 2298.20,
        stop_loss: 2293.00,
        take_profit_1: 2308.00,
        take_profit_2: 2313.00,
        risk_reward_ratio: 3.0,
        position_size: 0.1,
        risk_percentage: 1,
        setup_type: 'Liquidity Sweep',
        market_structure: 'BOS',
        confluence_factors: ['FVG', 'Order Block'],
        confidence_score: 0.9,
        h4_context: 'Uptrend',
        h1_context: 'Breakout',
        m15_context: 'Continuation',
        session: 'NY_OVERLAP',
        created_at: new Date(Date.now() - 7200000).toISOString(),
        updated_at: new Date(Date.now() - 7200000).toISOString(),
        status: 'EXECUTED'
      }
    ];
  }

  private generateMockPerformanceMetrics(): PerformanceMetrics {
    return {
      date: new Date().toISOString().split('T')[0],
      instrument: 'XAUUSD',
      total_signals: 25,
      total_trades: 18,
      winning_trades: 12,
      losing_trades: 6,
      win_rate: 0.67,
      average_rr: 1.8,
      total_pips: 485,
      total_profit_loss: 3250,
      largest_win: 850,
      largest_loss: 320,
      max_drawdown: 1200,
      sharpe_ratio: 1.4
    };
  }
}