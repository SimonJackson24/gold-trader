// Copyright (c) 2024 Simon Callaghan. All rights reserved.

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