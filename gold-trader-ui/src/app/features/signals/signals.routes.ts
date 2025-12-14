import { Routes } from '@angular/router';
import { SignalsComponent } from './signals.component';

export const signalsRoutes: Routes = [
  {
    path: '',
    component: SignalsComponent,
    data: {
      title: 'Signals',
      description: 'Trading signals and notifications'
    }
  }
];