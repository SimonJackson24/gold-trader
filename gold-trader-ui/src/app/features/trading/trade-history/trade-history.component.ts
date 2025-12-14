import { Component, OnInit, ChangeDetectionStrategy, ViewChild } from '@angular/core';
import { CommonModule, CurrencyPipe, DatePipe } from '@angular/common';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-trade-history',
  standalone: true,
  imports: [
    CommonModule,
    CurrencyPipe,
    DatePipe,
    MatCardModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule
  ],
  template: `
    <div class="trade-history-container" role="region" aria-label="Trade history">
      <mat-card class="trade-history-card">
        <mat-card-header>
          <mat-card-title>Trade History</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="table-container">
            <table mat-table [dataSource]="dataSource" matSort aria-label="Trade history table">
              <ng-container matColumnDef="symbol">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>Symbol</th>
                <td mat-cell *matCellDef="let trade">{{trade.symbol}}</td>
              </ng-container>

              <ng-container matColumnDef="type">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>Type</th>
                <td mat-cell *matCellDef="let trade">{{trade.type}}</td>
              </ng-container>

              <ng-container matColumnDef="volume">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>Volume</th>
                <td mat-cell *matCellDef="let trade">{{trade.volume}}</td>
              </ng-container>

              <ng-container matColumnDef="entryPrice">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>Entry Price</th>
                <td mat-cell *matCellDef="let trade">{{trade.entryPrice}}</td>
              </ng-container>

              <ng-container matColumnDef="exitPrice">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>Exit Price</th>
                <td mat-cell *matCellDef="let trade">{{trade.exitPrice}}</td>
              </ng-container>

              <ng-container matColumnDef="profit">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>Profit</th>
                <td mat-cell *matCellDef="let trade" [class.profit-positive]="trade.profit > 0" [class.profit-negative]="trade.profit < 0">
                  {{trade.profit | currency}}
                </td>
              </ng-container>

              <ng-container matColumnDef="timestamp">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>Time</th>
                <td mat-cell *matCellDef="let trade">{{trade.timestamp | date:'medium'}}</td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
            </table>
            <mat-paginator [pageSizeOptions]="[5, 10, 25, 100]" aria-label="Select trade history page"></mat-paginator>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['./trade-history.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TradeHistoryComponent implements OnInit {
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  dataSource = new MatTableDataSource<any>([]);
  displayedColumns: string[] = ['symbol', 'type', 'volume', 'entryPrice', 'exitPrice', 'profit', 'timestamp'];
  tradeHistory$: Observable<any[]> = new Observable<any[]>();

  ngOnInit(): void {
    // TODO: Replace with actual trade history data from service
    const mockData = [
      { symbol: 'XAUUSD', type: 'BUY', volume: 0.1, entryPrice: 1950.50, exitPrice: 1955.75, profit: 52.50, timestamp: new Date() },
      { symbol: 'EURUSD', type: 'SELL', volume: 0.2, entryPrice: 1.1050, exitPrice: 1.1025, profit: 50.00, timestamp: new Date(Date.now() - 86400000) },
      { symbol: 'GBPUSD', type: 'BUY', volume: 0.15, entryPrice: 1.3020, exitPrice: 1.3080, profit: 90.00, timestamp: new Date(Date.now() - 172800000) },
    ];

    this.dataSource.data = mockData;
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }
}