// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { bootstrapApplication } from '@angular/platform-browser';
import { enableProdMode } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { importProvidersFrom } from '@angular/core';
import { JwtModule } from '@auth0/angular-jwt';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { AppComponent } from './app/app.component';
import { environment } from './environments/environment';
import { routes } from './app/app.routes';

// Guards
import { AuthGuard } from './app/core/guards/auth.guard';
import { RoleGuard } from './app/core/guards/role.guard';
import { PermissionGuard } from './app/core/guards/permission.guard';
import { AuthService } from './app/core/services/auth.service';

export function tokenGetter() {
  return localStorage.getItem('access_token');
}

if (environment.production) {
  enableProdMode();
}

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptorsFromDi()),
    importProvidersFrom(
      FormsModule,
      ReactiveFormsModule,
      JwtModule.forRoot({
        config: {
          tokenGetter: tokenGetter,
          allowedDomains: [environment.apiUrl ? new URL(environment.apiUrl).hostname : 'localhost:8000'],
          disallowedRoutes: ['http://localhost:8000/api/v1/auth/login']
        }
      })
    ),
    // Providers from AppModule
    AuthGuard,
    RoleGuard,
    PermissionGuard,
    AuthService
  ]
})
  .catch(err => console.error(err));