import { Routes } from '@angular/router';

export const tradingRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./trading-layout/trading-layout.component').then(m => m.TradingLayoutComponent),
    children: [
      { path: 'charts', loadChildren: () => import('./charts/charts.module').then(m => m.ChartsModule) },
      { path: 'orders', loadChildren: () => import('./order-management/order-management.module').then(m => m.OrderManagementModule) },
      { path: 'history', loadChildren: () => import('./trade-history/trade-history.module').then(m => m.TradeHistoryModule) },
      { path: '', redirectTo: 'charts', pathMatch: 'full' }
    ],
    data: {
      title: 'Trading',
      description: 'Live trading interface with charts and order management'
    }
  }
];