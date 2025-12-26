// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { FormBuilder, FormGroup } from '@angular/forms';

import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatTabsModule } from '@angular/material/tabs';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSortModule } from '@angular/material/sort';
import { MatTooltipModule } from '@angular/material/tooltip';

import { Subject } from 'rxjs';

import { WebSocketService, ConnectionStatus } from '@core/services/websocket.service';
import { TradingSignal } from '@core/models/trading.models';

@Component({
  selector: 'app-signals',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    DatePipe,
    DecimalPipe,
    MatSnackBarModule,
    MatCardModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatTabsModule,
    MatChipsModule,
    MatProgressBarModule,
    MatTableModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    MatSortModule,
    MatTooltipModule
  ],
  template: `
    <div class="signals-container">
      <div class="signals-header">
        <h1 class="page-title">Trading Signals</h1>
        <p class="page-subtitle">Real-time trading signals and alerts</p>
        <div class="connection-status" *ngIf="connectionStatus$ | async as status">
          <mat-icon [ngClass]="{
            'connected': status === ConnectionStatus.Connected,
            'reconnecting': status === ConnectionStatus.Reconnecting,
            'disconnected': status === ConnectionStatus.Disconnected
          }">
            {{ status === 'Connected' ? 'wifi' : 'wifi_off' }}
          </mat-icon>
          <span class="status-text">{{ status }}</span>
        </div>
      </div>

      <!-- Signal Filters -->
      <div class="filter-section">
        <mat-card class="filter-card">
          <mat-card-content>
            <form [formGroup]="filterForm" class="filter-form">
              <mat-form-field appearance="outline">
                <mat-label>Status</mat-label>
                <mat-select formControlName="status">
                  <mat-option value="">All Status</mat-option>
                  <mat-option value="ACTIVE">Active</mat-option>
                  <mat-option value="COMPLETED">Completed</mat-option>
                  <mat-option value="CANCELLED">Cancelled</mat-option>
                </mat-select>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Direction</mat-label>
                <mat-select formControlName="direction">
                  <mat-option value="">All Directions</mat-option>
                  <mat-option value="BUY">Buy</mat-option>
                  <mat-option value="SELL">Sell</mat-option>
                </mat-select>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Instrument</mat-label>
                <mat-select formControlName="instrument">
                  <mat-option value="">All Instruments</mat-option>
                  <mat-option value="XAUUSD">XAUUSD (Gold)</mat-option>
                  <mat-option value="EURUSD">EURUSD</mat-option>
                  <mat-option value="GBPUSD">GBPUSD</mat-option>
                </mat-select>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Time Range</mat-label>
                <mat-select formControlName="timeRange">
                  <mat-option value="1h">Last Hour</mat-option>
                  <mat-option value="24h">Last 24 Hours</mat-option>
                  <mat-option value="7d">Last 7 Days</mat-option>
                  <mat-option value="30d">Last 30 Days</mat-option>
                </mat-select>
              </mat-form-field>

              <button mat-raised-button color="primary" (click)="applyFilters()" [disabled]="isLoading">
                <mat-icon>filter_list</mat-icon>
                Apply Filters
              </button>

              <button mat-stroked-button color="accent" (click)="clearFilters()">
                <mat-icon>clear</mat-icon>
                Clear
              </button>
            </form>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- Signal Statistics -->
      <div class="stats-section">
        <mat-card class="stats-card">
          <mat-card-header>
            <mat-card-title>Signal Statistics</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ signalStats.total }}</div>
                <div class="stat-label">Total Signals</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ signalStats.active }}</div>
                <div class="stat-label">Active</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ signalStats.completed }}</div>
                <div class="stat-label">Completed</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ signalStats.winRate }}%</div>
                <div class="stat-label">Win Rate</div>
              </div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- Signals Tabs -->
      <div class="signals-tabs-section">
        <mat-card class="tabs-card">
          <mat-tab-group>
            <!-- Active Signals Tab -->
            <mat-tab label="Active Signals">
              <div class="tab-content">
                <div class="signals-list">
                  <mat-card class="signal-card" 
                           *ngFor="let signal of activeSignals" 
                           [class.buy-signal]="signal.direction === 'BUY'"
                           [class.sell-signal]="signal.direction === 'SELL'">
                    <mat-card-header>
                      <div class="signal-header">
                        <div class="signal-info">
                          <span class="signal-symbol">{{ signal.instrument }}</span>
                          <mat-chip [color]="signal.direction === 'BUY' ? 'primary' : 'warn'" selected>
                            {{ signal.direction }}
                          </mat-chip>
                        </div>
                        <div class="signal-time">
                          <mat-icon>schedule</mat-icon>
                          {{ signal.created_at | date:'short' }}
                        </div>
                      </div>
                    </mat-card-header>
                    <mat-card-content>
                      <div class="signal-details">
                        <div class="signal-price">
                          <span class="price-label">Entry:</span>
                          <span class="price-value">{{ signal.entry_price | number:'1.5' }}</span>
                        </div>
                        <div class="signal-targets">
                          <div class="target-item">
                            <span class="target-label">SL:</span>
                            <span class="target-value stop-loss">{{ signal.stop_loss | number:'1.5' }}</span>
                          </div>
                          <div class="target-item">
                            <span class="target-label">TP1:</span>
                            <span class="target-value take-profit">{{ signal.take_profit_1 | number:'1.5' }}</span>
                          </div>
                          <div class="target-item">
                            <span class="target-label">TP2:</span>
                            <span class="target-value take-profit">{{ signal.take_profit_2 | number:'1.5' }}</span>
                          </div>
                        </div>
                        <div class="signal-meta">
                          <div class="confidence">
                            <span class="confidence-label">Confidence:</span>
                            <mat-progress-bar mode="determinate" [value]="signal.confidence_score"></mat-progress-bar>
                            <span class="confidence-value">{{ signal.confidence_score }}%</span>
                          </div>
                          <div class="signal-strategy">
                            <span class="strategy-label">Strategy:</span>
                            <span class="strategy-value">{{ signal.setup_type }}</span>
                          </div>
                        </div>
                      </div>
                    </mat-card-content>
                    <mat-card-actions>
                      <button mat-raised-button 
                              color="primary" 
                              (click)="executeSignal(signal)"
                              [disabled]="signal.status !== 'ACTIVE'">
                        <mat-icon>play_arrow</mat-icon>
                        Execute
                      </button>
                      <button mat-stroked-button 
                              color="accent" 
                              (click)="viewSignalDetails(signal)">
                        <mat-icon>visibility</mat-icon>
                        Details
                      </button>
                      <button mat-stroked-button 
                              color="warn" 
                              (click)="dismissSignal(signal)">
                        <mat-icon>close</mat-icon>
                        Dismiss
                      </button>
                    </mat-card-actions>
                  </mat-card>
                </div>

                <div class="no-signals" *ngIf="!isLoading && activeSignals.length === 0">
                  <mat-icon>trending_up</mat-icon>
                  <h3>No active signals</h3>
                  <p>Check back later for new trading signals</p>
                </div>
              </div>
            </mat-tab>

            <!-- Signal History Tab -->
            <mat-tab label="Signal History">
              <div class="tab-content">
                <div class="table-container">
                  <table mat-table [dataSource]="signalsDataSource" matSort>
                    <!-- Symbol Column -->
                    <ng-container matColumnDef="instrument">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Instrument</th>
                      <td mat-cell *matCellDef="let signal">{{ signal.instrument }}</td>
                    </ng-container>

                    <!-- Direction Column -->
                    <ng-container matColumnDef="direction">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Direction</th>
                      <td mat-cell *matCellDef="let signal">
                        <mat-chip [color]="signal.direction === 'BUY' ? 'primary' : 'warn'" selected>
                          {{ signal.direction }}
                        </mat-chip>
                      </td>
                    </ng-container>

                    <!-- Entry Price Column -->
                    <ng-container matColumnDef="entry_price">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Entry Price</th>
                      <td mat-cell *matCellDef="let signal">{{ signal.entry_price | number:'1.5' }}</td>
                    </ng-container>

                    <!-- Status Column -->
                    <ng-container matColumnDef="status">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Status</th>
                      <td mat-cell *matCellDef="let signal">
                        <mat-chip [color]="getStatusColor(signal.status)" selected>
                          {{ signal.status }}
                        </mat-chip>
                      </td>
                    </ng-container>

                    <!-- Created At Column -->
                    <ng-container matColumnDef="created_at">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Created</th>
                      <td mat-cell *matCellDef="let signal">{{ signal.created_at | date:'short' }}</td>
                    </ng-container>

                    <!-- Actions Column -->
                    <ng-container matColumnDef="actions">
                      <th mat-header-cell *matHeaderCellDef>Actions</th>
                      <td mat-cell *matCellDef="let signal">
                        <button mat-icon-button (click)="viewSignalDetails(signal)" matTooltip="View Details">
                          <mat-icon>visibility</mat-icon>
                        </button>
                      </td>
                    </ng-container>

                    <tr mat-header-row *matHeaderRowDef="['instrument', 'direction', 'entry_price', 'status', 'created_at', 'actions']"></tr>
                    <tr mat-row *matRowDef="let row; columns: displayedSignalColumns;"></tr>
                  </table>
                </div>

                <mat-paginator 
                  [pageSizeOptions]="[10, 25, 50, 100]"
                  [pageSize]="signalPageSize"
                  (page)="onSignalPageChange($event)"
                  showFirstLastButtons>
                </mat-paginator>
              </div>
            </mat-tab>
          </mat-tab-group>
        </mat-card>
      </div>

      <div class="loading-overlay" *ngIf="isLoading">
        <mat-spinner diameter="50"></mat-spinner>
        <p>Loading signals...</p>
      </div>
    </div>
  `,
  styles: [`
    .signals-container {
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
    }

    .signals-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      flex-wrap: wrap;
      gap: 16px;
    }

    .page-title {
      font-size: 32px;
      font-weight: 600;
      color: #333;
      margin: 0;
    }

    .page-subtitle {
      font-size: 16px;
      color: #666;
      margin: 0;
    }

    .connection-status {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .connection-status .connected {
      color: #4caf50;
    }
    
    .connection-status .reconnecting {
      color: #ff9800;
    }

    .connection-status .disconnected {
      color: #f44336;
    }

    .status-text {
      font-weight: 500;
      color: #666;
    }

    .filter-section {
      margin-bottom: 24px;
    }

    .filter-form {
      display: flex;
      gap: 16px;
      align-items: end;
      flex-wrap: wrap;
    }

    .stats-section {
      margin-bottom: 24px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 16px;
      padding: 16px 0;
    }

    .stat-item {
      text-align: center;
      padding: 16px;
      background: #f5f5f5;
      border-radius: 8px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #333;
      margin-bottom: 4px;
    }

    .stat-label {
      font-size: 12px;
      color: #666;
      font-weight: 500;
    }

    .signals-tabs-section {
      margin-bottom: 24px;
    }

    .tab-content {
      padding: 20px;
    }

    .signals-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .signal-card {
      border-left: 4px solid #ccc;
      transition: all 0.3s ease;
    }

    .signal-card.buy-signal {
      border-left-color: #4caf50;
    }

    .signal-card.sell-signal {
      border-left-color: #f44336;
    }

    .signal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
    }

    .signal-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .signal-symbol {
      font-size: 18px;
      font-weight: 600;
      color: #333;
    }

    .signal-time {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #666;
      font-size: 14px;
    }

    .signal-details {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .signal-price {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .price-label {
      font-weight: 500;
      color: #666;
    }

    .price-value {
      font-size: 18px;
      font-weight: 600;
      color: #333;
    }

    .signal-targets {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }

    .target-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .target-label {
      font-weight: 500;
      color: #666;
    }

    .target-value {
      font-weight: 600;
    }

    .target-value.stop-loss {
      color: #f44336;
    }

    .target-value.take-profit {
      color: #4caf50;
    }

    .signal-meta {
      display: flex;
      gap: 24px;
      align-items: center;
      flex-wrap: wrap;
    }

    .confidence {
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;
      min-width: 150px;
    }

    .confidence-label {
      font-weight: 500;
      color: #666;
    }

    .confidence-value {
      font-weight: 600;
      color: #333;
      margin-left: 8px;
    }

    .signal-strategy {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .strategy-label {
      font-weight: 500;
      color: #666;
    }

    .strategy-value {
      font-weight: 600;
      color: #333;
    }

    .table-container {
      overflow-x: auto;
      min-height: 300px;
    }

    .no-signals {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px;
      color: #666;
      text-align: center;
    }

    .no-signals mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      margin-bottom: 16px;
      opacity: 0.5;
    }

    .no-signals h3 {
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 500;
    }

    .no-signals p {
      margin: 0;
      font-size: 14px;
    }

    .loading-overlay {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px;
      color: #666;
    }

    .loading-overlay p {
      margin-top: 16px;
      font-size: 16px;
    }

    @media (max-width: 768px) {
      .signals-container {
        padding: 16px;
      }
      
      .signals-header {
        flex-direction: column;
        align-items: stretch;
      }
      
      .filter-form {
        flex-direction: column;
        align-items: stretch;
      }
      
      .signal-header {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
      }
      
      .signal-targets {
        flex-direction: column;
        gap: 8px;
      }
      
      .signal-meta {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
      }
      
      .table-container {
        overflow-x: scroll;
      }
    }
  `]
})
export class SignalsComponent implements OnInit, OnDestroy {
  filterForm: FormGroup;
  
  signals: TradingSignal[] = [];
  activeSignals: TradingSignal[] = [];
  signalsDataSource = new MatTableDataSource<TradingSignal>();
  
  displayedSignalColumns: string[] = ['instrument', 'direction', 'entry_price', 'status', 'created_at', 'actions'];
  
  signalPageSize = 25;
  private fb = inject(FormBuilder);
  private webSocketService = inject(WebSocketService);
  private snackBar = inject(MatSnackBar);

  private destroy$ = new Subject<void>();
  
  signalStats = {
    total: 0,
    active: 0,
    completed: 0,
    winRate: 0
  };

  currentSignalPage = 0;
  totalSignals = 0;
  
  isLoading = false;
  connectionStatus$ = this.webSocketService.connectionStatus$;
  ConnectionStatus = ConnectionStatus;

  constructor() {
    this.filterForm = this.fb.group({
      status: [''],
      direction: [''],
      instrument: [''],
      timeRange: ['24h'],
      minConfidence: [0]
    });
  }

  ngOnInit(): void {
    this.loadSignals();
    // WebSocket signals are now handled by the service
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadSignals(): void {
    this.isLoading = true;
    
    // Simulate API call
    setTimeout(() => {
      this.generateMockSignals();
      this.isLoading = false;
    }, 1500);
  }

  applyFilters(): void {
    this.loadSignals();
    this.snackBar.open('Filters applied', 'Close', { duration: 2000 });
  }

  clearFilters(): void {
    this.filterForm.reset({
      status: '',
      direction: '',
      instrument: '',
      timeRange: '24h',
      minConfidence: 0
    });
    this.loadSignals();
  }

  executeSignal(signal: TradingSignal): void {
    this.snackBar.open(`Executing signal for ${signal.instrument}...`, 'Close', {
      duration: 2000
    });
    
    // Simulate signal execution
    setTimeout(() => {
      this.snackBar.open(`Signal executed successfully!`, 'Close', {
        duration: 3000,
        panelClass: ['success-snackbar']
      });
      this.loadSignals();
    }, 2000);
  }

  viewSignalDetails(signal: TradingSignal): void {
    this.snackBar.open(`Viewing details for signal ${signal.signal_id}`, 'Close', {
      duration: 3000
    });
  }

  dismissSignal(signal: TradingSignal): void {
    this.snackBar.open(`Signal dismissed`, 'Close', { duration: 2000 });
    // Remove from active signals
    this.activeSignals = this.activeSignals.filter(s => s.signal_id !== signal.signal_id);
  }

  onSignalPageChange(event: any): void {
    this.signalPageSize = event.pageSize;
    this.currentSignalPage = event.pageIndex;
    this.loadSignals();
  }

  getStatusColor(status: string): 'primary' | 'accent' | 'warn' {
    switch (status) {
      case 'ACTIVE':
        return 'primary';
      case 'COMPLETED':
        return 'accent';
      case 'CANCELLED':
        return 'warn';
      default:
        return 'primary';
    }
  }

  private generateMockSignals(): void {
    const mockSignals: TradingSignal[] = [];
    const statuses = ['ACTIVE', 'COMPLETED', 'CANCELLED'];
    const directions = ['BUY', 'SELL'];
    const strategies = ['SMC', 'Breakout', 'Trend Following', 'Mean Reversion'];
    
    for (let i = 0; i < 50; i++) {
      const isBuy = Math.random() > 0.5;
      const entryPrice = isBuy ? 1985.50 + Math.random() * 10 : 1985.50 - Math.random() * 10;
      
      mockSignals.push({
        signal_id: `signal_${i + 1}`,
        instrument: 'XAUUSD',
        direction: directions[Math.floor(Math.random() * directions.length)] as any,
        entry_price: entryPrice,
        stop_loss: isBuy ? entryPrice - 20 : entryPrice + 20,
        take_profit_1: isBuy ? entryPrice + 30 : entryPrice - 30,
        take_profit_2: isBuy ? entryPrice + 50 : entryPrice - 50,
        risk_reward_ratio: 1.5 + Math.random() * 2,
        position_size: 0.1 + Math.random() * 0.4,
        risk_percentage: 1 + Math.random() * 2,
        setup_type: strategies[Math.floor(Math.random() * strategies.length)],
        market_structure: 'BOS',
        confluence_factors: ['FVG', 'Liquidity', 'Structure'],
        confidence_score: 70 + Math.random() * 30,
        h4_context: 'Bullish',
        h1_context: 'Bullish',
        m15_context: 'Range',
        session: 'LONDON',
        status: statuses[Math.floor(Math.random() * statuses.length)] as any,
        created_at: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString(),
        updated_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
      });
    }
    
    this.signals = mockSignals;
    this.activeSignals = mockSignals.filter(s => s.status === 'ACTIVE');
    this.signalsDataSource.data = mockSignals;
    
    // Update statistics
    this.signalStats = {
      total: mockSignals.length,
      active: this.activeSignals.length,
      completed: mockSignals.filter(s => s.status === 'EXECUTED').length,
      winRate: 68.5 // Mock win rate
    };
  }
}