import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MaterialModule } from '../../shared/material.module';
import { authRoutes } from './auth.routes';

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(authRoutes),
    FormsModule,
    ReactiveFormsModule,
    MaterialModule
  ]
})
export class AuthModule {}