import { Component, ViewChild } from '@angular/core';
import { RouterModule } from '@angular/router';
import { MaterialModule } from './shared/material.module';
import { NavigationComponent } from './core/components/navigation/navigation.component';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-root',
  template: `
    <div class="app-container" role="main">
      <app-navigation class="app-navigation"></app-navigation>
      <div class="app-content">
        <div class="toolbar">
          <button class="menu-button" (click)="navigation.toggleNavigation()">
            <mat-icon>menu</mat-icon>
          </button>
          <span class="toolbar-title">Gold Trader</span>
          <div class="toolbar-spacer"></div>
          <div class="connection-status">
            <div class="status-dot" [class.connected]="true"></div>
            <span class="status-text">Connected</span>
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
  imports: [RouterModule, MaterialModule, NavigationComponent, MatIconModule]
})
export class AppComponent {
  title = 'gold-trader-ui';

  @ViewChild(NavigationComponent) navigation!: NavigationComponent;
}