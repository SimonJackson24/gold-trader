import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MaterialModule } from '../../shared/material.module';

import { SignalsComponent } from './signals.component';
import { signalsRoutes } from './signals.routes';

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(signalsRoutes)
  ]
})
export class SignalsModule {}