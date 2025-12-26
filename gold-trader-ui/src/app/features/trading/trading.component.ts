// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-trading',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule
  ],
  template: `
    <div class="trading-container" role="main" aria-label="Trading platform">
      <router-outlet></router-outlet>
    </div>
  `,
  styles: [`
    .trading-container {
      width: 100%;
      height: 100%;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TradingComponent {}