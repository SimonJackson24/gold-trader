import { CommonModule } from '@angular/common';
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ViewChild } from '@angular/core';
import { Observable, Subject, combineLatest } from 'rxjs';
import { takeUntil, tap, switchMap, map } from 'rxjs/operators';
import { MarketDataService } from '../../../core/services/market-data.service';
import { ChartData, Timeframe, ChartConfig, ChartOverlay, TechnicalIndicator, PriceTick } from '../../../core/models/trading.models';
import { ChartComponent as PtChartComponent } from '../../../../libs/proprietary-charts/src/lib/chart.component';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-trading-charts',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatChipsModule,
    PtChartComponent
  ],
  template: `
    <div class="chart-container" role="region" aria-label="Trading charts">
      <mat-card class="chart-card">
        <mat-card-header>
          <mat-card-title>XAUUSD - {{ selectedTimeframe }}</mat-card-title>
          <mat-card-subtitle>
            <mat-chip-listbox aria-label="Timeframe selection">
              <mat-chip-option
                *ngFor="let tf of timeframes"
                [selected]="selectedTimeframe === tf"
                (click)="changeTimeframe(tf)"
                role="button"
                [attr.aria-label]="'Switch to ' + tf + ' timeframe'"
              >
                {{ tf }}
              </mat-chip-option>
            </mat-chip-listbox>
          </mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <pt-chart
            #chart
            [data]="candles"
            [config]="chartConfig"
            [overlays]="overlays"
            [indicators]="indicators"
            [aria-label]="'XAUUSD price chart with ' + selectedTimeframe + ' timeframe'"
            (onChartClick)="handleChartClick($event)"
            (onDrawingComplete)="handleDrawingComplete($event)"
            (timeframeChange)="handleTimeframeChange($event)"
          ></pt-chart>
        </mat-card-content>
      </mat-card>

      <div class="chart-controls" role="group" aria-label="Chart controls">
        <mat-card class="indicator-card">
          <mat-card-header>
            <mat-card-title>Indicators</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <mat-chip-listbox aria-label="Indicator selection">
              <mat-chip-option
                *ngFor="let indicator of indicators"
                [selected]="indicator.visible"
                (click)="toggleIndicator(indicator.id)"
                role="button"
                [attr.aria-label]="'Toggle ' + indicator.name + ' indicator'"
              >
                {{ indicator.name }}
              </mat-chip-option>
            </mat-chip-listbox>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styleUrls: ['./charts.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ChartsComponent implements OnInit, OnDestroy {
  @ViewChild('chart') chart!: PtChartComponent;

  private destroy$ = new Subject<void>();

  // Chart data
  candles: ChartData[] = [];
  overlays: ChartOverlay[] = [];
  indicators: TechnicalIndicator[] = [];
  selectedTimeframe: Timeframe = Timeframe.M15;
  lastPrice: number | null = null;

  // Chart configuration
  chartConfig: ChartConfig;

  // Available timeframes
  readonly timeframes = [
    Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.M30,
    Timeframe.H1, Timeframe.H4, Timeframe.D1
  ];

  constructor(private marketDataService: MarketDataService) {
    this.chartConfig = this.marketDataService.getDefaultChartConfig();
  }

  ngOnInit(): void {
    this.loadInitialData();
    this.setupSubscriptions();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load initial chart data
   */
  private loadInitialData(): void {
    // Load historical candles
    this.marketDataService.getHistoricalCandles('XAUUSD', this.selectedTimeframe)
      .pipe(takeUntil(this.destroy$))
      .subscribe(candles => {
        this.candles = candles;
        this.marketDataService.updateCandles(candles);
      });

    // Load technical indicators
    this.marketDataService.getTechnicalIndicators('XAUUSD', this.selectedTimeframe)
      .pipe(takeUntil(this.destroy$))
      .subscribe((indicators: TechnicalIndicator[]) => {
        this.indicators = indicators;
        this.marketDataService.updateIndicators(indicators);
      });

    // Load Smart Money Concepts analysis
    this.marketDataService.getSmartMoneyAnalysis('XAUUSD', this.selectedTimeframe)
      .pipe(takeUntil(this.destroy$))
      .subscribe();
  }

  /**
   * Setup subscriptions for real-time updates
   */
  private setupSubscriptions(): void {
    // Subscribe to candles updates
    this.marketDataService.onCandlesUpdate()
      .pipe(takeUntil(this.destroy$))
      .subscribe(candles => {
        this.candles = candles;
      });

    // Subscribe to overlays updates (Smart Money Concepts)
    this.marketDataService.onOverlaysUpdate()
      .pipe(takeUntil(this.destroy$))
      .subscribe(overlays => {
        this.overlays = overlays;
      });

    // Subscribe to indicators updates
    this.marketDataService.onIndicatorsUpdate()
      .pipe(takeUntil(this.destroy$))
      .subscribe(indicators => {
        this.indicators = indicators;
      });

    // Subscribe to price ticks for real-time updates
    this.marketDataService.onPriceTick()
      .pipe(takeUntil(this.destroy$))
      .subscribe(tick => {
        this.handlePriceTick(tick);
      });
  }

  /**
   * Handle incoming price tick
   * @param tick Price tick data
   */
  private handlePriceTick(tick: PriceTick): void {
    this.lastPrice = tick.last;

    // Update the last candle with the new price
    if (this.candles.length > 0) {
      const lastCandle = { ...this.candles[this.candles.length - 1] };

      // Update high/low if needed
      if (tick.last > lastCandle.high) {
        lastCandle.high = tick.last;
      }
      if (tick.last < lastCandle.low) {
        lastCandle.low = tick.last;
      }

      // Update close price
      lastCandle.close = tick.last;

      // Update the candles array
      const updatedCandles = [...this.candles];
      updatedCandles[this.candles.length - 1] = lastCandle;
      this.candles = updatedCandles;
      this.marketDataService.updateCandles(updatedCandles);
    }
  }

  /**
   * Change timeframe
   * @param timeframe New timeframe
   */
  changeTimeframe(timeframe: Timeframe): void {
    this.selectedTimeframe = timeframe;
    this.chartConfig.timeframe = timeframe;

    // Reload data for the new timeframe
    this.loadInitialData();
  }

  /**
   * Toggle indicator visibility
   * @param indicatorId Indicator ID
   */
  toggleIndicator(indicatorId: string): void {
    this.indicators = this.indicators.map(indicator => {
      if (indicator.id === indicatorId) {
        return { ...indicator, visible: !indicator.visible };
      }
      return indicator;
    });
    this.marketDataService.updateIndicators(this.indicators);
  }

  /**
   * Handle chart click event
   * @param event Chart click event
   */
  handleChartClick(event: { x: number; y: number }): void {
    console.log('Chart clicked at:', event);
    // Could be used for placing orders or annotations
  }

  /**
   * Handle drawing completion
   * @param drawing Completed drawing
   */
  handleDrawingComplete(drawing: any): void {
    console.log('Drawing completed:', drawing);
    // Could save drawings to user preferences or send to server
  }

  /**
   * Handle timeframe change from chart controls
   * @param timeframe New timeframe
   */
  handleTimeframeChange(timeframe: string): void {
    const tf = timeframe as Timeframe;
    if (this.timeframes.includes(tf)) {
      this.changeTimeframe(tf);
    }
  }
}