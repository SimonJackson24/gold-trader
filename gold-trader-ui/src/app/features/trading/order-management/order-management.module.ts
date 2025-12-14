import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MaterialModule } from '../../../shared/material.module';

import { OrderManagementComponent } from './order-management.component';

@NgModule({
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MaterialModule,
    RouterModule.forChild([
      { path: '', component: OrderManagementComponent, data: { title: 'Order Management' } }
    ]),
    OrderManagementComponent
  ]
})
export class OrderManagementModule {}