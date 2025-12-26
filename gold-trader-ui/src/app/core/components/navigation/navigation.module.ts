// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';

@NgModule({
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule
  ],
  exports: []
})
export class NavigationModule { }