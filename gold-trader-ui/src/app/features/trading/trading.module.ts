// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatTabsModule } from '@angular/material/tabs';
import { tradingRoutes } from './trading.routes';

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(tradingRoutes),
    MatTabsModule
  ],
  exports: [
    RouterModule
  ]
})
export class TradingModule {}