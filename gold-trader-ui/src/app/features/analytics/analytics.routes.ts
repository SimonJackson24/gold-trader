import { Routes } from '@angular/router';
import { AnalyticsComponent } from './analytics.component';

export const analyticsRoutes: Routes = [
  {
    path: '',
    component: AnalyticsComponent,
    data: {
      title: 'Analytics',
      description: 'Trading performance analytics and reports'
    }
  }
];