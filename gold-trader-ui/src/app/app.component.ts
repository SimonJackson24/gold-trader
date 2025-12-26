// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, ViewChild, inject } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Observable } from 'rxjs';
import { NavigationComponent } from './core/components/navigation/navigation.component';
import { MatIconModule } from '@angular/material/icon';
import { WebSocketService, ConnectionStatus } from './core/services/websocket.service';

@Component({
  selector: 'app-root',
  template: `
    <div class="app-container" role="main">
      <app-navigation class="app-navigation" #navigation></app-navigation>
      <div class="app-content">
        <div class="toolbar">
          <button class="menu-button" (click)="navigation.toggleNavigation()">
            <mat-icon>menu</mat-icon>
          </button>
          <span class="toolbar-title">Gold Trader</span>
          <div class="toolbar-spacer"></div>
          <div class="connection-status" *ngIf="connectionStatus$ | async as status">
            <div class="status-dot" [ngClass]="{
              'connected': status === ConnectionStatus.Connected,
              'connecting': status === ConnectionStatus.Connecting || status === ConnectionStatus.Reconnecting,
              'disconnected': status === ConnectionStatus.Disconnected
            }"></div>
            <span class="status-text">{{ status }}</span>
          </div>
        </div>
        <div class="main-content">
          <router-outlet></router-outlet>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./app.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    NavigationComponent,
    MatIconModule
  ]
})
export class AppComponent {
  title = 'gold-trader-ui';
  
  // Expose enum to the template
  ConnectionStatus = ConnectionStatus;

  @ViewChild(NavigationComponent) navigation!: NavigationComponent;

  private webSocketService = inject(WebSocketService);
  connectionStatus$: Observable<ConnectionStatus> = this.webSocketService.connectionStatus$;

  constructor() {}
}