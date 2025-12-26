// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';


import { AuthService } from '@core/services/auth.service';

interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    trading: boolean;
    account: boolean;
  };
  trading: {
    defaultVolume: number;
    defaultStopLoss: number;
    defaultTakeProfit: number;
    confirmTrades: boolean;
    autoClose: boolean;
  };
  display: {
    compactMode: boolean;
    showGrid: boolean;
    animationSpeed: 'slow' | 'normal' | 'fast';
  };
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    MatCardModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatSnackBarModule
  ],
  template: `
    <div class="settings-container">
      <div class="settings-header">
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">Manage your account and application preferences</p>
      </div>

      <form [formGroup]="settingsForm" class="settings-form">
        <!-- Profile Section -->
        <mat-card class="settings-section">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>person</mat-icon>
              Profile Settings
            </mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="form-row">
              <mat-form-field appearance="outline" class="full-width">
                <mat-label>Display Name</mat-label>
                <input matInput formControlName="displayName" placeholder="Enter your display name">
              </mat-form-field>
            </div>

            <div class="form-row">
              <mat-form-field appearance="outline" class="full-width">
                <mat-label>Email</mat-label>
                <input matInput formControlName="email" placeholder="Enter your email">
              </mat-form-field>
            </div>

            <div class="form-row">
              <mat-form-field appearance="outline" class="full-width">
                <mat-label>Phone Number</mat-label>
                <input matInput formControlName="phoneNumber" placeholder="Enter your phone number">
              </mat-form-field>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Appearance Section -->
        <mat-card class="settings-section">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>palette</mat-icon>
              Appearance
            </mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="form-row">
              <mat-form-field appearance="outline">
                <mat-label>Theme</mat-label>
                <mat-select formControlName="theme">
                  <mat-option value="light">Light</mat-option>
                  <mat-option value="dark">Dark</mat-option>
                  <mat-option value="auto">Auto</mat-option>
                </mat-select>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Language</mat-label>
                <mat-select formControlName="language">
                  <mat-option value="en">English</mat-option>
                  <mat-option value="es">Spanish</mat-option>
                  <mat-option value="fr">French</mat-option>
                  <mat-option value="de">German</mat-option>
                </mat-select>
              </mat-form-field>
            </div>

            <div class="form-row">
              <mat-form-field appearance="outline">
                <mat-label>Timezone</mat-label>
                <mat-select formControlName="timezone">
                  <mat-option value="UTC">UTC</mat-option>
                  <mat-option value="EST">Eastern Time</mat-option>
                  <mat-option value="PST">Pacific Time</mat-option>
                  <mat-option value="CET">Central European Time</mat-option>
                </mat-select>
              </mat-form-field>
            </div>

            <div class="form-row">
              <mat-slide-toggle formControlName="compactMode">
                Compact Mode
              </mat-slide-toggle>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Notifications Section -->
        <mat-card class="settings-section">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>notifications</mat-icon>
              Notifications
            </mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="form-row">
              <mat-slide-toggle formControlName="emailNotifications">
                Email Notifications
              </mat-slide-toggle>
            </div>

            <div class="form-row">
              <mat-slide-toggle formControlName="pushNotifications">
                Push Notifications
              </mat-slide-toggle>
            </div>

            <div class="form-row">
              <mat-slide-toggle formControlName="tradingNotifications">
                Trading Alerts
              </mat-slide-toggle>
            </div>

            <div class="form-row">
              <mat-slide-toggle formControlName="accountNotifications">
                Account Updates
              </mat-slide-toggle>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Trading Preferences Section -->
        <mat-card class="settings-section">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>trending_up</mat-icon>
              Trading Preferences
            </mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="form-row">
              <mat-form-field appearance="outline">
                <mat-label>Default Volume (lots)</mat-label>
                <input matInput type="number" formControlName="defaultVolume" min="0.01" step="0.01">
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Default Stop Loss (pips)</mat-label>
                <input matInput type="number" formControlName="defaultStopLoss" min="1">
              </mat-form-field>
            </div>

            <div class="form-row">
              <mat-form-field appearance="outline">
                <mat-label>Default Take Profit (pips)</mat-label>
                <input matInput type="number" formControlName="defaultTakeProfit" min="1">
              </mat-form-field>
            </div>

            <div class="form-row">
              <mat-slide-toggle formControlName="confirmTrades">
                Confirm All Trades
              </mat-slide-toggle>
            </div>

            <div class="form-row">
              <mat-slide-toggle formControlName="autoClose">
                Auto-Close on Stop Loss/Take Profit
              </mat-slide-toggle>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Security Section -->
        <mat-card class="settings-section">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>security</mat-icon>
              Security
            </mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="form-row">
              <mat-slide-toggle formControlName="twoFactorAuth">
                Two-Factor Authentication
              </mat-slide-toggle>
            </div>

            <div class="form-row">
              <mat-slide-toggle formControlName="sessionTimeout">
                Session Timeout Protection
              </mat-slide-toggle>
            </div>

            <div class="form-row">
              <button mat-stroked-button color="warn" (click)="changePassword()">
                <mat-icon>lock</mat-icon>
                Change Password
              </button>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Actions Section -->
        <div class="settings-actions">
          <button mat-raised-button 
                  color="primary" 
                  (click)="saveSettings()" 
                  [disabled]="settingsForm.invalid || isSaving">
            <mat-icon>save</mat-icon>
            <span *ngIf="!isSaving">Save Settings</span>
            <mat-spinner *ngIf="isSaving" diameter="20"></mat-spinner>
          </button>

          <button mat-stroked-button color="accent" (click)="resetSettings()">
            <mat-icon>refresh</mat-icon>
            Reset to Defaults
          </button>

          <button mat-stroked-button color="warn" (click)="exportSettings()">
            <mat-icon>download</mat-icon>
            Export Settings
          </button>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .settings-container {
      padding: 24px;
      max-width: 800px;
      margin: 0 auto;
    }

    .settings-header {
      margin-bottom: 32px;
      text-align: center;
    }

    .page-title {
      font-size: 32px;
      font-weight: 600;
      color: #333;
      margin: 0 0 8px 0;
    }

    .page-subtitle {
      font-size: 16px;
      color: #666;
      margin: 0;
    }

    .settings-form {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .settings-section {
      margin-bottom: 16px;
    }

    .settings-section mat-card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
    }

    .form-row {
      display: flex;
      gap: 16px;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .full-width {
      width: 100%;
    }

    .settings-actions {
      display: flex;
      gap: 16px;
      justify-content: center;
      padding: 24px 0;
      flex-wrap: wrap;
    }

    .settings-actions button {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 150px;
    }

    mat-spinner {
      margin: 0 auto;
    }

    @media (max-width: 768px) {
      .settings-container {
        padding: 16px;
      }
      
      .form-row {
        flex-direction: column;
        align-items: stretch;
      }
      
      .settings-actions {
        flex-direction: column;
        align-items: stretch;
      }
      
      .settings-actions button {
        width: 100%;
      }
    }
  `]
})
export class SettingsComponent implements OnInit {
  settingsForm: FormGroup;
  isSaving = false;

  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private snackBar = inject(MatSnackBar);

  constructor() {
    this.settingsForm = this.fb.group({
      // Profile Settings
      displayName: [''],
      email: ['', [Validators.email]],
      phoneNumber: [''],
      
      // Appearance Settings
      theme: ['light'],
      language: ['en'],
      timezone: ['UTC'],
      compactMode: [false],
      
      // Notification Settings
      emailNotifications: [true],
      pushNotifications: [true],
      tradingNotifications: [true],
      accountNotifications: [true],
      
      // Trading Preferences
      defaultVolume: [0.1, [Validators.min(0.01)]],
      defaultStopLoss: [20, [Validators.min(1)]],
      defaultTakeProfit: [40, [Validators.min(1)]],
      confirmTrades: [true],
      autoClose: [true],
      
      // Security Settings
      twoFactorAuth: [false],
      sessionTimeout: [true]
    });
  }

  ngOnInit(): void {
    this.loadUserSettings();
  }

  loadUserSettings(): void {
    // Simulate loading user settings
    const mockSettings = {
      displayName: 'John Doe',
      email: 'john.doe@example.com',
      phoneNumber: '+1234567890',
      theme: 'light',
      language: 'en',
      timezone: 'UTC',
      compactMode: false,
      emailNotifications: true,
      pushNotifications: true,
      tradingNotifications: true,
      accountNotifications: true,
      defaultVolume: 0.1,
      defaultStopLoss: 20,
      defaultTakeProfit: 40,
      confirmTrades: true,
      autoClose: true,
      twoFactorAuth: false,
      sessionTimeout: true
    };

    this.settingsForm.patchValue(mockSettings);
  }

  saveSettings(): void {
    if (this.settingsForm.valid) {
      this.isSaving = true;
      
      // Simulate API call
      setTimeout(() => {
        this.isSaving = false;
        this.snackBar.open('Settings saved successfully!', 'Close', {
          duration: 3000,
          panelClass: ['success-snackbar']
        });
      }, 2000);
    }
  }

  resetSettings(): void {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      this.settingsForm.reset({
        displayName: '',
        email: '',
        phoneNumber: '',
        theme: 'light',
        language: 'en',
        timezone: 'UTC',
        compactMode: false,
        emailNotifications: true,
        pushNotifications: true,
        tradingNotifications: true,
        accountNotifications: true,
        defaultVolume: 0.1,
        defaultStopLoss: 20,
        defaultTakeProfit: 40,
        confirmTrades: true,
        autoClose: true,
        twoFactorAuth: false,
        sessionTimeout: true
      });
      
      this.snackBar.open('Settings reset to defaults', 'Close', { duration: 2000 });
    }
  }

  exportSettings(): void {
    const settings = this.settingsForm.value;
    const dataStr = JSON.stringify(settings, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'trading-settings.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    this.snackBar.open('Settings exported successfully', 'Close', { duration: 2000 });
  }

  changePassword(): void {
    this.snackBar.open('Password change dialog would open here', 'Close', { duration: 2000 });
  }
}