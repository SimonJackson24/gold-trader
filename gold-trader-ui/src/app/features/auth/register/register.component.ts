// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';


import { AuthService } from '@core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    RouterModule,
    MatSnackBarModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule,
    MatButtonModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="register-container">
      <mat-card class="register-card">
        <mat-card-header>
          <mat-card-title class="register-title">Create Account</mat-card-title>
          <mat-card-subtitle>Join the Gold Trader platform</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <form [formGroup]="registerForm" (ngSubmit)="onSubmit()" class="register-form">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Username</mat-label>
              <input matInput formControlName="username" placeholder="Choose a username">
              <mat-error *ngIf="registerForm.get('username')?.hasError('required')">
                Username is required
              </mat-error>
              <mat-error *ngIf="registerForm.get('username')?.hasError('minlength')">
                Username must be at least 3 characters
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Email</mat-label>
              <input matInput type="email" formControlName="email" placeholder="Enter your email">
              <mat-error *ngIf="registerForm.get('email')?.hasError('required')">
                Email is required
              </mat-error>
              <mat-error *ngIf="registerForm.get('email')?.hasError('email')">
                Please enter a valid email
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Password</mat-label>
              <input matInput type="password" formControlName="password" placeholder="Create a password">
              <mat-error *ngIf="registerForm.get('password')?.hasError('required')">
                Password is required
              </mat-error>
              <mat-error *ngIf="registerForm.get('password')?.hasError('minlength')">
                Password must be at least 6 characters
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Confirm Password</mat-label>
              <input matInput type="password" formControlName="confirmPassword" placeholder="Confirm your password">
              <mat-error *ngIf="registerForm.get('confirmPassword')?.hasError('required')">
                Please confirm your password
              </mat-error>
              <mat-error *ngIf="registerForm.hasError('passwordMismatch')">
                Passwords do not match
              </mat-error>
            </mat-form-field>

            <mat-checkbox formControlName="agreeToTerms" class="terms-checkbox">
              I agree to the <a href="#" (click)="showTerms($event)">Terms and Conditions</a>
            </mat-checkbox>
            <mat-error *ngIf="registerForm.get('agreeToTerms')?.hasError('required')" class="error-message">
              You must agree to the terms and conditions
            </mat-error>
          </form>
        </mat-card-content>
        <mat-card-actions class="register-actions">
          <button mat-raised-button 
                  color="primary" 
                  (click)="onSubmit()" 
                  [disabled]="registerForm.invalid || isLoading"
                  class="register-button">
            <span *ngIf="!isLoading">Create Account</span>
            <mat-spinner *ngIf="isLoading" diameter="20"></mat-spinner>
          </button>
          <a mat-button routerLink="/login" class="login-link">
            Already have an account? Login
          </a>
        </mat-card-actions>
      </mat-card>
    </div>
  `,
  styles: [`
    .register-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
    }

    .register-card {
      max-width: 450px;
      width: 100%;
      padding: 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .register-title {
      font-size: 24px;
      font-weight: 600;
      color: #333;
      text-align: center;
      margin-bottom: 8px;
    }

    .register-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .full-width {
      width: 100%;
    }

    .terms-checkbox {
      margin: 16px 0;
    }

    .terms-checkbox a {
      color: #667eea;
      text-decoration: none;
    }

    .terms-checkbox a:hover {
      text-decoration: underline;
    }

    .error-message {
      color: #f44336;
      font-size: 12px;
      margin-top: -8px;
      margin-bottom: 8px;
    }

    .register-actions {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 16px 0 0 0;
    }

    .register-button {
      width: 100%;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .login-link {
      text-align: center;
      color: #666;
      text-decoration: none;
    }

    .login-link:hover {
      color: #667eea;
    }

    mat-spinner {
      margin: 0 auto;
    }
  `]
})
export class RegisterComponent implements OnInit {
  registerForm: FormGroup;
  isLoading = false;

  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private snackBar = inject(MatSnackBar);

  constructor() {
    this.registerForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]],
      agreeToTerms: [false, Validators.required]
    }, { validators: this.passwordMatchValidator });
  }

  ngOnInit(): void {
    // Check if user is already authenticated
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
    }
  }

  passwordMatchValidator(form: FormGroup): { passwordMismatch: boolean } | null {
    const password = form.get('password')?.value;
    const confirmPassword = form.get('confirmPassword')?.value;
    return password && confirmPassword && password !== confirmPassword 
      ? { passwordMismatch: true } 
      : null;
  }

  onSubmit(): void {
    if (this.registerForm.valid) {
      this.isLoading = true;
      const registrationData = {
        username: this.registerForm.value.username,
        email: this.registerForm.value.email,
        password: this.registerForm.value.password
      };
      
      // Simulate registration API call
      setTimeout(() => {
        this.isLoading = false;
        this.snackBar.open('Account created successfully! Please login.', 'Close', {
          duration: 3000,
          panelClass: ['success-snackbar']
        });
        this.router.navigate(['/login']);
      }, 2000);
    }
  }

  showTerms(event: Event): void {
    event.preventDefault();
    this.snackBar.open('Terms and Conditions would open in a modal', 'Close', {
      duration: 3000
    });
  }
}