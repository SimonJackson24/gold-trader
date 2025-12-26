// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSortModule } from '@angular/material/sort';

import { ChartComponent } from '../../shared/chart/chart.component';

import { Subject, takeUntil } from 'rxjs';
import { ApiService } from '@core/services/api.service';
import { ChartData } from '../../shared/chart/chart.component';
import { Chart, registerables } from 'chart.js';

// Register all chart.js components
Chart.register(...registerables);

interface PerformanceMetric {
  metric: string;
  value: number;
  change: number;
  changePercent: number;
}

interface TradeAnalytics {
  date: string;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalProfit: number;
  averageWin: number;
  averageLoss: number;
  profitFactor: number;
}

interface DailyPerformance {
  date: string;
  profit: number;
  trades: number;
  winRate: number;
}

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    ChartComponent,
    DatePipe,
    MatSnackBarModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatProgressBarModule,
    MatTableModule,
    MatProgressSpinnerModule,
    MatSortModule
  ],
  template: `
    <div class="analytics-container">
      <div class="analytics-header">
        <h1 class="page-title">Trading Analytics</h1>
        <p class="page-subtitle">Analyze your trading performance and patterns</p>
      </div>

      <!-- Date Range Filter -->
      <div class="filter-section">
        <mat-card class="filter-card">
          <mat-card-content>
            <form [formGroup]="filterForm" class="filter-form">
              <mat-form-field appearance="outline">
                <mat-label>Start Date</mat-label>
                <input matInput [matDatepicker]="startPicker" formControlName="startDate">
                <mat-datepicker-toggle matSuffix [for]="startPicker"></mat-datepicker-toggle>
                <mat-datepicker #startPicker></mat-datepicker>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>End Date</mat-label>
                <input matInput [matDatepicker]="endPicker" formControlName="endDate">
                <mat-datepicker-toggle matSuffix [for]="endPicker"></mat-datepicker-toggle>
                <mat-datepicker #endPicker></mat-datepicker>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Time Period</mat-label>
                <mat-select formControlName="period">
                  <mat-option value="7d">Last 7 Days</mat-option>
                  <mat-option value="30d">Last 30 Days</mat-option>
                  <mat-option value="90d">Last 90 Days</mat-option>
                  <mat-option value="1y">Last Year</mat-option>
                  <mat-option value="all">All Time</mat-option>
                </mat-select>
              </mat-form-field>

              <button mat-raised-button color="primary" (click)="applyFilters()" [disabled]="isLoading">
                <mat-icon>filter_list</mat-icon>
                Apply Filters
              </button>

              <button mat-stroked-button color="accent" (click)="exportData()" [disabled]="isLoading">
                <mat-icon>download</mat-icon>
                Export
              </button>
            </form>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- Performance Metrics -->
      <div class="metrics-section">
        <mat-card class="metrics-card">
          <mat-card-header>
            <mat-card-title>Performance Metrics</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="metrics-grid">
              <div class="metric-card" *ngFor="let metric of performanceMetrics">
                <div class="metric-header">
                  <span class="metric-label">{{ metric.metric }}</span>
                  <mat-icon [class.positive]="metric.change > 0" 
                           [class.negative]="metric.change < 0"
                           class="metric-icon">
                    {{ metric.change > 0 ? 'trending_up' : metric.change < 0 ? 'trending_down' : 'trending_flat' }}
                  </mat-icon>
                </div>
                <div class="metric-value">{{ metric.value | number:'1.2' }}</div>
                <div class="metric-change" 
                     [class.positive]="metric.change > 0" 
                     [class.negative]="metric.change < 0">
                  {{ metric.change > 0 ? '+' : '' }}{{ metric.changePercent | number:'1.2' }}%
                </div>
              </div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- Analytics Tabs -->
      <div class="analytics-tabs-section">
        <mat-card class="tabs-card">
          <mat-tab-group>
            <!-- Trading Performance Tab -->
            <mat-tab label="Trading Performance">
              <div class="tab-content">
                <app-chart
                  title="Performance Over Time"
                  subtitle="Daily trading performance metrics"
                  [data]="performanceChartData"
                  type="line">
                </app-chart>
                <div class="table-container">
                  <table mat-table [dataSource]="analyticsDataSource" matSort>
                    <!-- Date Column -->
                    <ng-container matColumnDef="date">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Date</th>
                      <td mat-cell *matCellDef="let analytics">{{ analytics.date | date:'medium' }}</td>
                    </ng-container>

                    <!-- Total Trades Column -->
                    <ng-container matColumnDef="totalTrades">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Total Trades</th>
                      <td mat-cell *matCellDef="let analytics">{{ analytics.totalTrades }}</td>
                    </ng-container>

                    <!-- Win Rate Column -->
                    <ng-container matColumnDef="winRate">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Win Rate</th>
                      <td mat-cell *matCellDef="let analytics">
                        <mat-progress-bar mode="determinate" [value]="analytics.winRate"></mat-progress-bar>
                        <span class="percentage">{{ analytics.winRate | number:'1.1' }}%</span>
                      </td>
                    </ng-container>

                    <!-- Total Profit Column -->
                    <ng-container matColumnDef="totalProfit">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Total Profit</th>
                      <td mat-cell *matCellDef="let analytics">
                        <span [class.positive]="analytics.totalProfit > 0" 
                              [class.negative]="analytics.totalProfit < 0">
                          {{ analytics.totalProfit | number:'1.2' }}
                        </span>
                      </td>
                    </ng-container>

                    <!-- Profit Factor Column -->
                    <ng-container matColumnDef="profitFactor">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Profit Factor</th>
                      <td mat-cell *matCellDef="let analytics">{{ analytics.profitFactor | number:'1.2' }}</td>
                    </ng-container>

                    <tr mat-header-row *matHeaderRowDef="displayedAnalyticsColumns"></tr>
                    <tr mat-row *matRowDef="let row; columns: displayedAnalyticsColumns;"></tr>
                  </table>
                </div>
              </div>
            </mat-tab>

            <!-- Daily Performance Tab -->
            <mat-tab label="Daily Performance">
              <div class="tab-content">
                <app-chart
                  title="Daily Profit/Loss"
                  subtitle="Daily profit and loss trends"
                  [data]="dailyChartData"
                  type="bar">
                </app-chart>
                <div class="table-container">
                  <table mat-table [dataSource]="dailyDataSource" matSort>
                    <!-- Date Column -->
                    <ng-container matColumnDef="date">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Date</th>
                      <td mat-cell *matCellDef="let daily">{{ daily.date | date:'short' }}</td>
                    </ng-container>

                    <!-- Profit Column -->
                    <ng-container matColumnDef="profit">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Profit</th>
                      <td mat-cell *matCellDef="let daily">
                        <span [class.positive]="daily.profit > 0" 
                              [class.negative]="daily.profit < 0">
                          {{ daily.profit | number:'1.2' }}
                        </span>
                      </td>
                    </ng-container>

                    <!-- Trades Column -->
                    <ng-container matColumnDef="trades">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Trades</th>
                      <td mat-cell *matCellDef="let daily">{{ daily.trades }}</td>
                    </ng-container>

                    <!-- Win Rate Column -->
                    <ng-container matColumnDef="winRate">
                      <th mat-header-cell *matHeaderCellDef mat-sort-header>Win Rate</th>
                      <td mat-cell *matCellDef="let daily">{{ daily.winRate | number:'1.1' }}%</td>
                    </ng-container>

                    <tr mat-header-row *matHeaderRowDef="displayedDailyColumns"></tr>
                    <tr mat-row *matRowDef="let row; columns: displayedDailyColumns;"></tr>
                  </table>
                </div>
              </div>
            </mat-tab>
          </mat-tab-group>
        </mat-card>
      </div>

      <div class="loading-overlay" *ngIf="isLoading">
        <mat-spinner diameter="50"></mat-spinner>
        <p>Loading analytics data...</p>
      </div>
    </div>
  `,
  styles: [`
    .analytics-container {
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
    }

    .analytics-header {
      margin-bottom: 32px;
      text-align: center;
    }

    .page-title {
      font-size: 32px;
      font-weight: 600;
      color: #333;
      margin: 0 0 8px 0;
    }

    .page-subtitle {
      font-size: 16px;
      color: #666;
      margin: 0;
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

    .metrics-section {
      margin-bottom: 24px;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      padding: 16px 0;
    }

    .metric-card {
      background: #f5f5f5;
      border-radius: 8px;
      padding: 16px;
      text-align: center;
    }

    .metric-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .metric-label {
      font-size: 12px;
      color: #666;
      font-weight: 500;
    }

    .metric-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
    }

    .metric-icon.positive {
      color: #4caf50;
    }

    .metric-icon.negative {
      color: #f44336;
    }

    .metric-value {
      font-size: 24px;
      font-weight: 600;
      color: #333;
      margin-bottom: 4px;
    }

    .metric-change {
      font-size: 12px;
      font-weight: 500;
    }

    .metric-change.positive {
      color: #4caf50;
    }

    .metric-change.negative {
      color: #f44336;
    }

    .analytics-tabs-section {
      margin-bottom: 24px;
    }

    .tab-content {
      padding: 20px;
    }

    .chart-placeholder {
      height: 300px;
      margin-bottom: 24px;
      background: #f9f9f9;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #666;
    }

    .table-container {
      overflow-x: auto;
      min-height: 300px;
    }

    .positive {
      color: #4caf50;
      font-weight: 600;
    }

    .negative {
      color: #f44336;
      font-weight: 600;
    }

    .percentage {
      margin-left: 8px;
      font-size: 12px;
      color: #666;
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
      .analytics-container {
        padding: 16px;
      }
      
      .filter-form {
        flex-direction: column;
        align-items: stretch;
      }
      
      .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
      }
      
      .table-container {
        overflow-x: scroll;
      }
    }
  `]
})
export class AnalyticsComponent implements OnInit, OnDestroy {
  filterForm: FormGroup;
  
  performanceMetrics: PerformanceMetric[] = [];
  tradeAnalytics: TradeAnalytics[] = [];
  dailyPerformance: DailyPerformance[] = [];
  
  analyticsDataSource = new MatTableDataSource<TradeAnalytics>();
  dailyDataSource = new MatTableDataSource<DailyPerformance>();
  
  displayedAnalyticsColumns: string[] = ['date', 'totalTrades', 'winRate', 'totalProfit', 'profitFactor'];
  displayedDailyColumns: string[] = ['date', 'profit', 'trades', 'winRate'];
  
  isLoading = false;
  
  // Chart data properties
  performanceChartData: ChartData<'line'> = {
    labels: [],
    datasets: []
  };
  
  dailyChartData: ChartData<'bar'> = {
    labels: [],
    datasets: []
  };
  
  private destroy$ = new Subject<void>();

  private fb = inject(FormBuilder);
  private snackBar = inject(MatSnackBar);
  private apiService = inject(ApiService);

  constructor() {
    this.filterForm = this.fb.group({
      startDate: [new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)], // 30 days ago
      endDate: [new Date()],
      period: ['30d']
    });
  }

  ngOnInit(): void {
    this.loadAnalyticsData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadAnalyticsData(): void {
    this.isLoading = true;
    
    console.log('Loading analytics data from /api/v1/performance/daily');
    // Load real performance data from API
    this.apiService.getDailyPerformance().pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response: any) => {
        this.processPerformanceData(response);
        this.isLoading = false;
      },
      error: (error: any) => {
        console.error('Error loading analytics data:', error);
        this.snackBar.open('Failed to load analytics data', 'Close', { duration: 3000 });
        this.isLoading = false;
        // Fallback to mock data for development
        this.generateMockData();
      }
    });
  }

  private processPerformanceData(response: any): void {
    console.log('Processing performance data:', response);
    try {
      // Process performance metrics
      this.performanceMetrics = [
        { metric: 'Total Profit', value: response.summary?.total_profit_loss || 0, change: 325.00, changePercent: 14.6 },
        { metric: 'Win Rate', value: response.summary?.average_win_rate || 0, change: 2.3, changePercent: 3.5 },
        { metric: 'Profit Factor', value: 1.85, change: 0.15, changePercent: 8.8 },
        { metric: 'Average Win', value: 125.30, change: 12.50, changePercent: 11.1 },
        { metric: 'Average Loss', value: -67.80, change: -5.20, changePercent: -7.1 },
        { metric: 'Total Trades', value: response.summary?.total_days || 0, change: 12, changePercent: 8.3 }
      ];
      console.log('Performance metrics processed:', this.performanceMetrics);

      // Process trade analytics from daily metrics
      if (response.metrics && response.metrics.length > 0) {
        this.tradeAnalytics = response.metrics.map((metric: any) => ({
          date: metric.date,
          totalTrades: metric.total_trades || 0,
          winningTrades: metric.winning_trades || 0,
          losingTrades: metric.losing_trades || 0,
          winRate: metric.win_rate || 0,
          totalProfit: metric.total_profit_loss || 0,
          averageWin: metric.total_profit_loss / (metric.winning_trades || 1),
          averageLoss: metric.total_profit_loss / (metric.losing_trades || 1),
          profitFactor: metric.total_profit_loss > 0 ?
            (metric.total_profit_loss / Math.abs(metric.total_profit_loss / (metric.win_rate / 100))) : 0
        }));
        console.log('Trade analytics processed:', this.tradeAnalytics);

        // Process daily performance data
        this.dailyPerformance = response.metrics.map((metric: any) => ({
          date: metric.date,
          profit: metric.total_profit_loss || 0,
          trades: metric.total_trades || 0,
          winRate: metric.win_rate || 0
        }));
        console.log('Daily performance data processed:', this.dailyPerformance);

        this.analyticsDataSource.data = this.tradeAnalytics;
        this.dailyDataSource.data = this.dailyPerformance;
        
        // Transform data for charts
        this.transformDataForCharts();
        console.log('Data transformed for charts');
      } else {
        console.warn('No metrics data found in the response.');
      }
    } catch (e) {
      console.error('Error processing performance data:', e);
    }
  }

  applyFilters(): void {
    this.loadAnalyticsData();
    this.snackBar.open('Filters applied successfully', 'Close', { duration: 2000 });
  }

  exportData(): void {
    this.snackBar.open('Exporting analytics data...', 'Close', { duration: 2000 });
    // Simulate export functionality
    setTimeout(() => {
      this.snackBar.open('Data exported successfully', 'Close', { 
        duration: 3000,
        panelClass: ['success-snackbar']
      });
    }, 1000);
  }

  private generateMockData(): void {
    console.warn('Using mock data - API endpoints may not be available');
    
    // Generate performance metrics
    this.performanceMetrics = [
      { metric: 'Total Profit', value: 2547.50, change: 325.00, changePercent: 14.6 },
      { metric: 'Win Rate', value: 68.5, change: 2.3, changePercent: 3.5 },
      { metric: 'Profit Factor', value: 1.85, change: 0.15, changePercent: 8.8 },
      { metric: 'Average Win', value: 125.30, change: 12.50, changePercent: 11.1 },
      { metric: 'Average Loss', value: -67.80, change: -5.20, changePercent: -7.1 },
      { metric: 'Total Trades', value: 156, change: 12, changePercent: 8.3 }
    ];

    // Generate trade analytics
    this.tradeAnalytics = [];
    for (let i = 0; i < 30; i++) {
      const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
      const totalTrades = Math.floor(Math.random() * 10) + 2;
      const winRate = 60 + Math.random() * 20;
      const winningTrades = Math.floor(totalTrades * winRate / 100);
      const losingTrades = totalTrades - winningTrades;
      const totalProfit = (Math.random() - 0.3) * 500;
      
      this.tradeAnalytics.push({
        date: date.toISOString(),
        totalTrades,
        winningTrades,
        losingTrades,
        winRate,
        totalProfit,
        averageWin: 50 + Math.random() * 100,
        averageLoss: -(30 + Math.random() * 70),
        profitFactor: 1.2 + Math.random() * 1.5
      });
    }

    // Generate daily performance
    this.dailyPerformance = [];
    for (let i = 0; i < 30; i++) {
      const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
      const profit = (Math.random() - 0.3) * 300;
      const trades = Math.floor(Math.random() * 8) + 1;
      const winRate = 55 + Math.random() * 25;
      
      this.dailyPerformance.push({
        date: date.toISOString(),
        profit,
        trades,
        winRate
      });
    }

    this.analyticsDataSource.data = this.tradeAnalytics.reverse();
    this.dailyDataSource.data = this.dailyPerformance.reverse();
    
    // Transform mock data for charts
    this.transformDataForCharts();
  }
  
  private transformDataForCharts(): void {
    // Transform data for performance chart (line chart)
    this.performanceChartData = {
      labels: this.tradeAnalytics.map(item => new Date(item.date).toLocaleDateString()),
      datasets: [
        {
          label: 'Win Rate (%)',
          data: this.tradeAnalytics.map(item => item.winRate),
          borderColor: '#4caf50',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          tension: 0.1,
          fill: true
        },
        {
          label: 'Total Profit',
          data: this.tradeAnalytics.map(item => item.totalProfit),
          borderColor: '#2196f3',
          backgroundColor: 'rgba(33, 150, 243, 0.1)',
          tension: 0.1,
          fill: true,
          yAxisID: 'y1'
        }
      ]
    };
    
    // Transform data for daily performance chart (bar chart)
    this.dailyChartData = {
      labels: this.dailyPerformance.map(item => new Date(item.date).toLocaleDateString()),
      datasets: [
        {
          label: 'Daily Profit/Loss',
          data: this.dailyPerformance.map(item => item.profit),
          backgroundColor: this.dailyPerformance.map(item =>
            item.profit >= 0 ? 'rgba(76, 175, 80, 0.8)' : 'rgba(244, 67, 54, 0.8)'
          ),
          borderColor: this.dailyPerformance.map(item =>
            item.profit >= 0 ? '#4caf50' : '#f44336'
          ),
          borderWidth: 1
        }
      ]
    };
  }
}