// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import {
  Component,
  OnInit,
  OnDestroy,
  OnChanges,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  ElementRef,
  ChangeDetectionStrategy,
  SimpleChanges
} from '@angular/core';

import { Observable, Subject, fromEvent, merge } from 'rxjs';
import { takeUntil, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  ChartData,
  ChartConfig,
  ChartOverlay,
  ChartPoint,
  FairValueGap,
  OrderBlock,
  LiquidityPool,
  LiquiditySweep,
  MarketStructure,
  DrawingTool,
  TechnicalIndicator,
  Timeframe
} from '@core/models/trading.models';

@Component({
  selector: 'pt-chart',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  template: `
    <div class="chart-container" #chartContainer>
      <canvas #chartCanvas
              class="chart-canvas"
              role="img"
              aria-label="Trading chart for XAUUSD"
              aria-describedby="chart-description">
      </canvas>
      <div id="chart-description" class="sr-only">
        Interactive trading chart showing price movements, technical indicators, and trading signals
      </div>
      <div class="chart-controls">
        <div class="timeframe-selector">
          <select 
            [value]="selectedTimeframe" 
            (change)="onTimeframeChange($event)"
            class="form-control">
            <option *ngFor="let tf of timeframes" [value]="tf">
              {{tf}}
            </option>
          </select>
        </div>
        <div class="chart-tools">
          <button 
            *ngFor="let tool of drawingTools" 
            class="tool-btn"
            [class.active]="selectedTool === tool.type"
            (click)="selectTool(tool)"
            [title]="tool.name">
            <i [class]="tool.icon"></i>
          </button>
        </div>
        <div class="overlays-toggle" role="group" aria-label="Chart overlays">
          <label class="checkbox-label">
            <input
              type="checkbox"
              [(ngModel)]="showFVG"
              (change)="toggleOverlay('fvg')"
              aria-describedby="fvg-desc">
            <span id="fvg-desc">Fair Value Gap</span>
          </label>
          <label class="checkbox-label">
            <input
              type="checkbox"
              [(ngModel)]="showOrderBlocks"
              (change)="toggleOverlay('orderBlock')"
              aria-describedby="ob-desc">
            <span id="ob-desc">Order Blocks</span>
          </label>
          <label class="checkbox-label">
            <input
              type="checkbox"
              [(ngModel)]="showLiquidity"
              (change)="toggleOverlay('liquidity')"
              aria-describedby="liq-desc">
            <span id="liq-desc">Liquidity</span>
          </label>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./chart.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ChartComponent implements OnInit, OnDestroy, OnChanges {
  @ViewChild('chartContainer', { static: true }) chartContainer!: ElementRef;
  @ViewChild('chartCanvas', { static: true }) chartCanvas!: ElementRef;
  
  @Input() data: ChartData[] = [];
  @Input() config: ChartConfig = {
    type: 'candlestick',
    timeframe: 'M15',
    showVolume: true,
    showGrid: true,
    showCrosshair: true,
    autoScale: true,
    backgroundColor: '#1a1a1a',
    gridColor: '#333333',
    upColor: '#00ff00',
    downColor: '#ff0000',
    volumeColor: '#666666'
  };
  @Input() overlays: ChartOverlay[] = [];
  @Input() indicators: TechnicalIndicator[] = [];
  
  @Output() onChartClick = new EventEmitter<{ x: number; y: number }>();
  @Output() onDrawingComplete = new EventEmitter<DrawingTool>();
  @Output() timeframeChange = new EventEmitter<string>();
  
  private canvas!: HTMLCanvasElement;
  private ctx!: CanvasRenderingContext2D;
  private resizeObserver!: ResizeObserver;
  private destroy$ = new Subject<void>();
  
  // Chart state - made public for template access
  selectedTimeframe = Timeframe.M15;
  showFVG = true;
  showOrderBlocks = true;
  showLiquidity = true;
  selectedTool: string | null = null;
  private isDrawing = false;
  private drawingStart: { x: number; y: number } | null = null;
  private currentDrawing: DrawingTool | null = null;
  private animationFrameId: number | null = null;
  private needsRedraw = false;
  
  // Chart dimensions
  private chartWidth = 0;
  private chartHeight = 0;
  private padding = { top: 20, right: 60, bottom: 60, left: 10 };
  
  // Price scaling
  private minPrice = 0;
  private maxPrice = 0;
  private priceRange = 0;
  private pixelsPerPoint = 0;
  
  // Time scaling
  private minTimestamp = 0;
  private maxTimestamp = 0;
  private timeRange = 0;
  private pixelsPerMillisecond = 0;
  
  readonly timeframes = [
    Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.M30,
    Timeframe.H1, Timeframe.H4, Timeframe.D1
  ];
  
  readonly drawingTools = [
    { type: 'trendline', name: 'Trend Line', icon: 'fas fa-chart-line' },
    { type: 'horizontal', name: 'Horizontal Line', icon: 'fas fa-minus' },
    { type: 'vertical', name: 'Vertical Line', icon: 'fas fa-minus' },
    { type: 'rectangle', name: 'Rectangle', icon: 'fas fa-square' },
    { type: 'fibonacci', name: 'Fibonacci', icon: 'fas fa-chart-area' }
  ];
  
  ngOnInit(): void {
    this.initializeChart();
    this.setupEventListeners();
  }
  
  ngOnChanges(changes: SimpleChanges): void {
    if (changes['data']) {
      this.updateChartData();
    }
    
    if (changes['overlays']) {
      this.renderOverlays();
    }
    
    if (changes['config']) {
      this.applyConfig();
    }
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }
  
  private initializeChart(): void {
    this.canvas = this.chartCanvas.nativeElement;
    this.ctx = this.canvas.getContext('2d')!;
    
    this.setupResizeObserver();
    this.calculateDimensions();
    this.clearChart();
    this.drawGrid();
    this.drawAxes();
  }
  
  private setupResizeObserver(): void {
    this.resizeObserver = new ResizeObserver(() => {
      this.calculateDimensions();
      this.clearChart();
      this.drawGrid();
      this.drawAxes();
      this.updateChartData();
      this.renderOverlays();
    });
    
    this.resizeObserver.observe(this.chartContainer.nativeElement);
  }
  
  private setupEventListeners(): void {
    // Mouse events for drawing and interaction
    const mouseDown$ = fromEvent<MouseEvent>(this.canvas, 'mousedown');
    const mouseMove$ = fromEvent<MouseEvent>(this.canvas, 'mousemove');
    const mouseUp$ = fromEvent<MouseEvent>(this.canvas, 'mouseup');
    const mouseClick$ = fromEvent<MouseEvent>(this.canvas, 'click');
    
    merge(mouseDown$, mouseMove$, mouseUp$, mouseClick$)
      .pipe(
        takeUntil(this.destroy$),
        debounceTime(10)
      )
      .subscribe((event: MouseEvent) => this.handleMouseEvent(event));
  }
  
  private handleMouseEvent(event: MouseEvent): void {
    const rect = this.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    switch (event.type) {
      case 'mousedown':
        if (this.selectedTool) {
          this.startDrawing(x, y);
        }
        break;
        
      case 'mousemove':
        if (this.isDrawing && this.drawingStart) {
          this.updateDrawing(x, y);
        }
        break;
        
      case 'mouseup':
        if (this.isDrawing) {
          this.finishDrawing();
        }
        break;
        
      case 'click':
        if (!this.selectedTool) {
          this.handleChartClick(x, y);
        }
        break;
    }
  }
  
  private startDrawing(x: number, y: number): void {
    this.isDrawing = true;
    this.drawingStart = { x, y };
    
    this.currentDrawing = {
      id: `drawing_${Date.now()}`,
      type: this.selectedTool as any,
      startPoint: { x, y },
      endPoint: { x, y },
      color: '#ffff00',
      width: 2,
      style: 'solid'
    };
  }
  
  private updateDrawing(x: number, y: number): void {
    if (!this.currentDrawing || !this.drawingStart) {
      return;
    }
    
    this.currentDrawing.endPoint = { x, y };
    this.scheduleRedraw();
  }
  
  private finishDrawing(): void {
    if (!this.currentDrawing) {
      return;
    }
    
    this.isDrawing = false;
    this.onDrawingComplete.emit(this.currentDrawing);
    this.currentDrawing = null;
    this.drawingStart = null;
  }
  
  private handleChartClick(x: number, y: number): void {
    const price = this.pixelToPrice(y);
    const timestamp = this.pixelToTime(x);
    
    this.onChartClick.emit({ x: timestamp, y: price });
  }
  
  private calculateDimensions(): void {
    const rect = this.chartContainer.nativeElement.getBoundingClientRect();
    this.chartWidth = rect.width - this.padding.left - this.padding.right;
    this.chartHeight = rect.height - this.padding.top - this.padding.bottom;
  }
  
  private calculatePriceScale(): void {
    if (this.data.length === 0) {
      return;
    }
    
    const prices = this.data.map(d => [d.open, d.high, d.low, d.close]).flat();
    this.minPrice = Math.min(...prices);
    this.maxPrice = Math.max(...prices);
    this.priceRange = this.maxPrice - this.minPrice;
    this.pixelsPerPoint = (this.chartHeight - 40) / this.priceRange; // Leave 40px for padding
  }
  
  private calculateTimeScale(): void {
    if (this.data.length === 0) {
      return;
    }
    
    const timestamps = this.data.map(d => new Date(d.timestamp).getTime());
    this.minTimestamp = Math.min(...timestamps);
    this.maxTimestamp = Math.max(...timestamps);
    this.timeRange = this.maxTimestamp - this.minTimestamp;
    this.pixelsPerMillisecond = (this.chartWidth - 80) / this.timeRange; // Leave 80px for labels
  }
  
  private clearChart(): void {
    this.ctx.fillStyle = this.config.backgroundColor;
    this.ctx.fillRect(0, 0, this.chartWidth, this.chartHeight);
  }
  
  private drawGrid(): void {
    if (!this.config.showGrid) {
      return;
    }
    
    this.ctx.strokeStyle = this.config.gridColor;
    this.ctx.lineWidth = 0.5;
    this.ctx.setLineDash([5, 5]);
    
    // Horizontal grid lines
    const horizontalLines = 10;
    for (let i = 0; i <= horizontalLines; i++) {
      const y = this.padding.top + (i * this.chartHeight / horizontalLines);
      this.ctx.beginPath();
      this.ctx.moveTo(this.padding.left, y);
      this.ctx.lineTo(this.chartWidth + this.padding.left, y);
      this.ctx.stroke();
    }
    
    // Vertical grid lines
    const verticalLines = 10;
    for (let i = 0; i <= verticalLines; i++) {
      const x = this.padding.left + (i * this.chartWidth / verticalLines);
      this.ctx.beginPath();
      this.ctx.moveTo(x, this.padding.top);
      this.ctx.lineTo(x, this.chartHeight + this.padding.top);
      this.ctx.stroke();
    }
  }
  
  private drawAxes(): void {
    this.ctx.strokeStyle = '#666666';
    this.ctx.lineWidth = 1;
    this.ctx.setLineDash([]);
    
    // X-axis (time)
    this.ctx.beginPath();
    this.ctx.moveTo(this.padding.left, this.chartHeight + this.padding.top);
    this.ctx.lineTo(this.chartWidth + this.padding.left, this.chartHeight + this.padding.top);
    this.ctx.stroke();
    
    // Y-axis (price)
    this.ctx.beginPath();
    this.ctx.moveTo(this.padding.left, this.padding.top);
    this.ctx.lineTo(this.padding.left, this.chartHeight + this.padding.top);
    this.ctx.stroke();
    
    // Draw axis labels
    this.drawAxisLabels();
  }
  
  private drawAxisLabels(): void {
    this.ctx.fillStyle = '#666666';
    this.ctx.font = '12px Arial';
    
    // Price labels on Y-axis
    const priceLabels = 5;
    for (let i = 0; i <= priceLabels; i++) {
      const price = this.minPrice + (i * this.priceRange / priceLabels);
      const y = this.priceToPixel(price);
      
      this.ctx.fillText(
        price.toFixed(2),
        5,
        y
      );
    }
    
    // Time labels on X-axis
    const timeLabels = 5;
    for (let i = 0; i <= timeLabels; i++) {
      const timestamp = this.minTimestamp + (i * this.timeRange / timeLabels);
      const x = this.timeToPixel(timestamp);
      const date = new Date(timestamp);
      
      this.ctx.fillText(
        date.toLocaleTimeString(),
        x,
        this.chartHeight + this.padding.top + 20
      );
    }
  }
  
  private updateChartData(): void {
    if (this.data.length === 0) {
      return;
    }
    
    this.calculatePriceScale();
    this.calculateTimeScale();
    this.drawData();
  }
  
  private drawData(): void {
    if (this.config.type === 'candlestick') {
      this.drawCandlesticks();
    } else if (this.config.type === 'line') {
      this.drawLineChart();
    } else if (this.config.type === 'area') {
      this.drawAreaChart();
    }
    
    if (this.config.showVolume) {
      this.drawVolume();
    }
  }
  
  private drawCandlesticks(): void {
    const candleWidth = (this.chartWidth - 80) / this.data.length; // Leave 80px for time axis
    
    this.data.forEach((candle, index) => {
      const x = this.timeToPixel(new Date(candle.timestamp).getTime());
      const yOpen = this.priceToPixel(candle.open);
      const yHigh = this.priceToPixel(candle.high);
      const yLow = this.priceToPixel(candle.low);
      const yClose = this.priceToPixel(candle.close);
      
      // Determine color
      const isGreen = candle.close >= candle.open;
      this.ctx.fillStyle = isGreen ? this.config.upColor : this.config.downColor;
      
      // Draw candle body
      const bodyTop = Math.min(yOpen, yClose);
      const bodyBottom = Math.max(yOpen, yClose);
      const bodyHeight = Math.abs(yClose - yOpen);
      
      this.ctx.fillRect(
        x - candleWidth / 2,
        Math.min(bodyTop, bodyBottom),
        candleWidth,
        bodyHeight
      );
      
      // Draw wicks
      this.ctx.strokeStyle = this.ctx.fillStyle;
      this.ctx.lineWidth = 1;
      this.ctx.beginPath();
      this.ctx.moveTo(x, yOpen);
      this.ctx.lineTo(x, yHigh);
      this.ctx.moveTo(x, yClose);
      this.ctx.lineTo(x, yLow);
      this.ctx.stroke();
    });
  }
  
  private drawLineChart(): void {
    this.ctx.strokeStyle = '#00ff00';
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    
    this.data.forEach((point, index) => {
      const x = this.timeToPixel(new Date(point.timestamp).getTime());
      const y = this.priceToPixel(point.close);
      
      if (index === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    });
    
    this.ctx.stroke();
  }
  
  private drawAreaChart(): void {
    // Implementation for area chart
    // Similar to line chart but with filled area
  }
  
  private drawVolume(): void {
    const volumeHeight = 40;
    const volumeY = this.chartHeight + this.padding.top + 10;
    
    this.data.forEach((candle, index) => {
      const x = this.timeToPixel(new Date(candle.timestamp).getTime());
      const barWidth = (this.chartWidth - 80) / this.data.length;
      const volume = candle.volume || 0;
      const maxVolume = Math.max(...this.data.map(c => c.volume || 0));
      const barHeight = (volume / maxVolume) * volumeHeight;
      
      this.ctx.fillStyle = '#666666';
      this.ctx.fillRect(
        x - barWidth / 2,
        volumeY - barHeight,
        barWidth,
        barHeight
      );
    });
  }
  
  private renderOverlays(): void {
    if (!this.overlays || this.overlays.length === 0) {
      return;
    }
    
    this.overlays.forEach(overlay => {
      if (!overlay.visible) {
        return;
      }
      
      switch (overlay.type) {
        case 'fvg':
          if (this.showFVG) {
            this.drawFVG(overlay.data as FairValueGap);
          }
          break;
          
        case 'orderBlock':
          if (this.showOrderBlocks) {
            this.drawOrderBlock(overlay.data as OrderBlock);
          }
          break;
          
        case 'liquidity':
          if (this.showLiquidity) {
            this.drawLiquidityPool(overlay.data as LiquidityPool);
          }
          break;
          
        case 'structure':
          this.drawMarketStructure(overlay.data as MarketStructure);
          break;
      }
    });
  }
  
  private drawFVG(fvg: FairValueGap): void {
    const startTime = new Date(fvg.start_time).getTime();
    const endTime = new Date(fvg.end_time).getTime();
    const xStart = this.timeToPixel(startTime);
    const xEnd = this.timeToPixel(endTime);
    const yTop = this.priceToPixel(fvg.top_price);
    const yBottom = this.priceToPixel(fvg.bottom_price);
    
    this.ctx.fillStyle = fvg.type === 'BULLISH' ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)';
    this.ctx.fillRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
    
    // Draw border
    this.ctx.strokeStyle = fvg.type === 'BULLISH' ? '#00ff00' : '#ff0000';
    this.ctx.lineWidth = 1;
    this.ctx.strokeRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
  }
  
  private drawOrderBlock(ob: OrderBlock): void {
    const startTime = new Date(ob.start_time).getTime();
    const endTime = new Date(ob.end_time).getTime();
    const xStart = this.timeToPixel(startTime);
    const xEnd = this.timeToPixel(endTime);
    const yTop = this.priceToPixel(ob.price);
    const yBottom = this.priceToPixel(ob.price - ob.range_size);
    
    this.ctx.fillStyle = ob.type === 'BULLISH' ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)';
    this.ctx.fillRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
    
    // Draw border
    this.ctx.strokeStyle = ob.type === 'BULLISH' ? '#00ff00' : '#ff0000';
    this.ctx.lineWidth = 2;
    this.ctx.strokeRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
  }
  
  private drawLiquidityPool(pool: LiquidityPool): void {
    const x = this.timeToPixel(new Date(pool.created_at).getTime());
    const y = this.priceToPixel(pool.price);
    const radius = 20;
    
    this.ctx.fillStyle = pool.pool_type === 'BUY_SIDE' ? 'rgba(0, 100, 255, 0.2)' : 'rgba(255, 100, 0, 0.2)';
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
    this.ctx.fill();
    
    // Draw border
    this.ctx.strokeStyle = pool.pool_type === 'BUY_SIDE' ? '#0066ff' : '#ff6600';
    this.ctx.lineWidth = 2;
    this.ctx.stroke();
  }
  
  private drawMarketStructure(structure: MarketStructure): void {
    const x = this.timeToPixel(new Date(structure.timestamp).getTime());
    const y = this.priceToPixel(structure.price);
    
    this.ctx.strokeStyle = structure.type === 'BOS' ? '#00ff00' : '#ff0000';
    this.ctx.lineWidth = 3;
    this.ctx.beginPath();
    this.ctx.moveTo(x - 10, y);
    this.ctx.lineTo(x, y);
    this.ctx.lineTo(x + 10, y);
    this.ctx.stroke();
  }
  
  private redrawChart(): void {
    if (!this.needsRedraw) {
      return;
    }
    
    this.needsRedraw = false;
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    
    this.animationFrameId = requestAnimationFrame(() => {
      this.clearChart();
      this.drawGrid();
      this.drawAxes();
      this.drawData();
      this.renderOverlays();
      this.drawUserDrawings();
    });
  }
  
  private drawUserDrawings(): void {
    // Draw user-created drawing tools
    // Implementation would store and render user drawings
  }
  
  private priceToPixel(price: number): number {
    if (this.priceRange === 0) {
      return this.chartHeight / 2;
    }
    
    const normalizedPrice = (price - this.minPrice) / this.priceRange;
    return this.chartHeight + this.padding.top - (normalizedPrice * (this.chartHeight - 40));
  }
  
  private timeToPixel(timestamp: number): number {
    if (this.timeRange === 0) {
      return this.chartWidth / 2;
    }
    
    const normalizedTime = (timestamp - this.minTimestamp) / this.timeRange;
    return this.padding.left + (normalizedTime * (this.chartWidth - 80));
  }
  
  private pixelToPrice(pixel: number): number {
    if (this.pixelsPerPoint === 0) {
      return 0;
    }
    
    const normalizedY = (this.chartHeight + this.padding.top - pixel) / (this.chartHeight - 40);
    return this.minPrice + (normalizedY * this.priceRange);
  }
  
  private pixelToTime(pixel: number): number {
    if (this.pixelsPerMillisecond === 0) {
      return 0;
    }
    
    const normalizedX = (pixel - this.padding.left) / (this.chartWidth - 80);
    return this.minTimestamp + (normalizedX * this.timeRange);
  }
  
  private applyConfig(): void {
    this.redrawChart();
  }
  
  // Made public for template access
  toggleOverlay(type: string): void {
    const overlay = this.overlays.find(o => o.type === type);
    if (overlay) {
      overlay.visible = !overlay.visible;
      this.scheduleRedraw();
    }
  }
  
  onTimeframeChange(event: any): void {
    this.selectedTimeframe = event.target.value;
    this.timeframeChange.emit(this.selectedTimeframe);
  }
  
  private scheduleRedraw(): void {
    this.needsRedraw = true;
  }
  
  private startAnimationLoop(): void {
    // Animation loop for smooth rendering
    const animate = () => {
      if (this.needsRedraw) {
        this.redrawChart();
      }
      this.animationFrameId = requestAnimationFrame(animate);
    };
    animate();
  }
  
  selectTool(tool: any): void {
    this.selectedTool = this.selectedTool === tool.type ? null : tool.type;
  }
}