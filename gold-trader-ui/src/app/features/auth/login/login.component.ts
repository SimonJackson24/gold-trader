import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { MaterialModule } from '../../../shared/material.module';
import { MatSnackBar } from '@angular/material/snack-bar';

import { AuthService } from '@core/services/auth.service';
import { LoginCredentials } from '@core/models/auth.models';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    MaterialModule,
    ReactiveFormsModule,
    FormsModule,
    RouterLink
  ],
  template: `
    <div class="login-container">
      <mat-card class="login-card">
        <mat-card-header>
          <mat-card-title class="login-title">Gold Trader Login</mat-card-title>
          <mat-card-subtitle>Access your trading account</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="login-form">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Username</mat-label>
              <input matInput formControlName="username" placeholder="Enter your username">
              <mat-error *ngIf="loginForm.get('username')?.hasError('required')">
                Username is required
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Password</mat-label>
              <input matInput type="password" formControlName="password" placeholder="Enter your password">
              <mat-error *ngIf="loginForm.get('password')?.hasError('required')">
                Password is required
              </mat-error>
            </mat-form-field>

            <mat-checkbox formControlName="rememberMe" class="remember-me">
              Remember me
            </mat-checkbox>
          </form>
        </mat-card-content>
        <mat-card-actions class="login-actions">
          <button mat-raised-button 
                  color="primary" 
                  (click)="onSubmit()" 
                  [disabled]="loginForm.invalid || isLoading"
                  class="login-button">
            <span *ngIf="!isLoading">Login</span>
            <mat-spinner *ngIf="isLoading" diameter="20"></mat-spinner>
          </button>
          <a mat-button routerLink="/register" class="register-link">
            Don't have an account? Register
          </a>
        </mat-card-actions>
      </mat-card>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
    }

    .login-card {
      max-width: 400px;
      width: 100%;
      padding: 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .login-title {
      font-size: 24px;
      font-weight: 600;
      color: #333;
      text-align: center;
      margin-bottom: 8px;
    }

    .login-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .full-width {
      width: 100%;
    }

    .remember-me {
      margin: 8px 0;
    }

    .login-actions {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 16px 0 0 0;
    }

    .login-button {
      width: 100%;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .register-link {
      text-align: center;
      color: #666;
      text-decoration: none;
    }

    .register-link:hover {
      color: #667eea;
    }

    mat-spinner {
      margin: 0 auto;
    }
  `]
})
export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      rememberMe: [false]
    });
  }

  ngOnInit(): void {
    // Check if user is already authenticated
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
    }
  }

  onSubmit(): void {
    if (this.loginForm.valid) {
      this.isLoading = true;
      const credentials: LoginCredentials = this.loginForm.value;
      
      this.authService.login(credentials).subscribe({
        next: () => {
          this.snackBar.open('Login successful!', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });
          this.router.navigate(['/dashboard']);
        },
        error: (error) => {
          this.isLoading = false;
          const errorMessage = error?.error?.message || 'Login failed. Please try again.';
          this.snackBar.open(errorMessage, 'Close', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
        },
        complete: () => {
          this.isLoading = false;
        }
      });
    }
  }
}