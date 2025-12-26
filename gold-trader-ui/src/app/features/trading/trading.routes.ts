// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Routes } from '@angular/router';

export const tradingRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./trading-layout/trading-layout.component').then(m => m.TradingLayoutComponent),
    children: [
      { path: 'charts', loadComponent: () => import('./charts/charts.component').then(m => m.ChartsComponent) },
      { path: 'orders', loadComponent: () => import('./order-management/order-management.component').then(m => m.OrderManagementComponent) },
      { path: 'history', loadComponent: () => import('./trade-history/trade-history.component').then(m => m.TradeHistoryComponent) },
      { path: '', redirectTo: 'charts', pathMatch: 'full' }
    ],
    data: {
      title: 'Trading',
      description: 'Live trading interface with charts and order management'
    }
  }
];