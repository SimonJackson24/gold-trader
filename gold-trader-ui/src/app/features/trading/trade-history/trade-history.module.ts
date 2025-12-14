import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MaterialModule } from '../../../shared/material.module';

import { TradeHistoryComponent } from './trade-history.component';

@NgModule({
  imports: [
    CommonModule,
    MaterialModule,
    RouterModule.forChild([
      { path: '', component: TradeHistoryComponent, data: { title: 'Trade History' } }
    ]),
    TradeHistoryComponent
  ]
})
export class TradeHistoryModule {}