import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MaterialModule } from '../../shared/material.module';

import { analyticsRoutes } from './analytics.routes';

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(analyticsRoutes),
    FormsModule,
    ReactiveFormsModule,
    MaterialModule
  ]
})
export class AnalyticsModule {}