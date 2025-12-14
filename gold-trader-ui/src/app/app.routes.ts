import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent) },
  { path: 'trading', loadChildren: () => import('./features/trading/trading.routes').then(m => m.tradingRoutes) },
  { path: 'signals', loadChildren: () => import('./features/signals/signals.routes').then(m => m.signalsRoutes) },
  { path: 'analytics', loadChildren: () => import('./features/analytics/analytics.routes').then(m => m.analyticsRoutes) },
  { path: 'settings', loadChildren: () => import('./features/settings/settings.routes').then(m => m.settingsRoutes) },
  { path: 'auth', loadChildren: () => import('./features/auth/auth.routes').then(m => m.authRoutes) },
  { path: '**', redirectTo: '/dashboard' }
];