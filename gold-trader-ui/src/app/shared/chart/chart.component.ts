import { Component, Input, OnChanges, SimpleChanges, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MaterialModule } from '../material.module';
import { Chart, ChartConfiguration, ChartType, ChartData, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

// Register Chart.js components
import { CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';

Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export type { ChartData };

@Component({
  selector: 'app-chart',
  standalone: true,
  imports: [CommonModule, MaterialModule, BaseChartDirective],
  template: `
    <div class="chart-container">
      <mat-card class="chart-card">
        <mat-card-header>
          <mat-card-title>{{ title }}</mat-card-title>
          <mat-card-subtitle *ngIf="subtitle">{{ subtitle }}</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="chart-wrapper">
            <canvas baseChart
                    [data]="chartData"
                    [options]="chartOptions"
                    [type]="type">
            </canvas>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .chart-container {
      width: 100%;
      height: 400px;
      margin: 16px 0;
    }

    .chart-card {
      height: 100%;
    }

    .chart-wrapper {
      position: relative;
      height: 350px;
      width: 100%;
    }

    canvas {
      max-height: 100%;
      max-width: 100%;
    }
  `]
})
export class ChartComponent implements OnChanges, AfterViewInit, OnDestroy {
  @Input() title: string = '';
  @Input() subtitle: string = '';
  @Input() data: any | null = null;
  @Input() type: 'line' | 'bar' = 'line';
  @Input() options: any | null = null;

  public chartData: ChartData<'line' | 'bar'> = {
    labels: [],
    datasets: []
  };
  public chartOptions: ChartOptions<'line' | 'bar'> = {};
  public chartType: ChartType = 'line';

  constructor() {}

  ngAfterViewInit(): void {
    this.updateChartData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['data'] || changes['type'] || changes['options']) {
      this.updateChartData();
    }
  }

  private updateChartData(): void {
    if (!this.data) return;

    this.chartData = this.data;
    this.chartType = (this.type as 'line' | 'bar');

    const defaultOptions: ChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      }
    };

    // Add scales for line/bar charts
    if (this.type === 'line' || this.type === 'bar') {
      defaultOptions.scales = {
        x: {
          type: 'category',
          display: true,
          title: {
            display: true,
            text: 'Date'
          }
        },
        y: {
          type: 'linear',
          display: true,
          title: {
            display: true,
            text: 'Value'
          }
        }
      };
    }

    this.chartOptions = this.options ? { ...defaultOptions, ...this.options } : defaultOptions;
  }

  ngOnDestroy(): void {
    // Chart cleanup is handled by ng2-charts
  }
}