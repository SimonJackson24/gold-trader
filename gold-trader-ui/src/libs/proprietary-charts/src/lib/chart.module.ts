// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartComponent } from './chart.component';

@NgModule({
  imports: [
    CommonModule,
    ChartComponent
  ],
  exports: [
    ChartComponent
  ]
})
export class ChartModule {}