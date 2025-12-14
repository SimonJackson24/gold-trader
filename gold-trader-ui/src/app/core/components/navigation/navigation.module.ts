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