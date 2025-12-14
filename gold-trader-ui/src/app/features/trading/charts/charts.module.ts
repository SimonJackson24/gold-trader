import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MaterialModule } from '../../../shared/material.module';
import { ChartModule } from '../../../../libs/proprietary-charts/src/lib/chart.module';
import { ChartsComponent } from './charts.component';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MaterialModule,
    ChartModule,
    RouterModule.forChild([
      { path: '', component: ChartsComponent }
    ]),
    ChartsComponent
  ]
})
export class ChartsModule {}