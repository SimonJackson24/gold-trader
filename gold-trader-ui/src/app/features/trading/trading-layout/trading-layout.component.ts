// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, ChangeDetectionStrategy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTabsModule } from '@angular/material/tabs';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-trading-layout',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    RouterModule
  ],
  template: `
    <div class="trading-layout" role="main" aria-label="Trading platform">
      <nav mat-tab-nav-bar class="trading-tabs" aria-label="Trading navigation">
        <a mat-tab-link
           *ngFor="let link of navLinks; let i = index"
           [routerLink]="link.path"
           routerLinkActive #rla="routerLinkActive"
           [active]="rla.isActive"
           [attr.aria-current]="rla.isActive ? 'page' : null"
           [attr.aria-selected]="rla.isActive"
           [attr.tabindex]="rla.isActive ? 0 : -1"
           (keydown)="onKeyDown($event, i)"
           #tabLink>
          {{link.label}}
        </a>
      </nav>

      <div class="trading-content">
        <router-outlet></router-outlet>
      </div>
    </div>
  `,
  styleUrls: ['./trading-layout.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TradingLayoutComponent {
  navLinks = [
    { path: 'charts', label: 'Charts' },
    { path: 'orders', label: 'Order Management' },
    { path: 'history', label: 'Trade History' }
  ];

  @HostListener('keydown.arrowRight', ['$event'])
  @HostListener('keydown.arrowLeft', ['$event'])
  onKeyDown(event: KeyboardEvent, currentIndex: number): void {
    // Handle right arrow key
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      const nextIndex = (currentIndex + 1) % this.navLinks.length;
      this.focusTab(nextIndex);
    }
    // Handle left arrow key
    else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      const prevIndex = (currentIndex - 1 + this.navLinks.length) % this.navLinks.length;
      this.focusTab(prevIndex);
    }
  }

  private focusTab(index: number): void {
    const tabLinks = document.querySelectorAll('.trading-tabs a[mat-tab-link]');
    if (tabLinks && tabLinks[index]) {
      (tabLinks[index] as HTMLElement).focus();
    }
  }
}