import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MaterialModule } from '../../shared/material.module';

import { SettingsComponent } from './settings.component';
import { settingsRoutes } from './settings.routes';

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(settingsRoutes)
  ]
})
export class SettingsModule {}