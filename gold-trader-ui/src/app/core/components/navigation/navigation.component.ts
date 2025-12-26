// Copyright (c) 2024 Simon Callaghan. All rights reserved.

import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { takeUntil, map, tap } from 'rxjs/operators';
import { AuthService, AuthStatus } from '@core/services/auth.service';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { User } from '@core/models/auth.models';

interface NavItem {
  id: string;
  label: string;
  icon: string;
  route?: string;
  children?: NavItem[];
  active?: boolean; // For submenu toggle state
  disabled?: boolean;
}

@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule
  ]
})
export class NavigationComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  private router = inject(Router);
  public authService = inject(AuthService);
  private breakpointObserver = inject(BreakpointObserver);

  // Navigation items
  navItems: NavItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: 'dashboard',
      route: '/dashboard'
    },
    {
      id: 'trading',
      label: 'Trading',
      icon: 'trending_up',
      active: false,
      children: [
        { id: 'charts', label: 'Charts', icon: 'show_chart', route: '/trading/charts' },
        { id: 'orders', label: 'Orders', icon: 'receipt_long', route: '/trading/orders' },
        { id: 'history', label: 'History', icon: 'history', route: '/trading/history' }
      ]
    },
    { id: 'analytics', label: 'Analytics', icon: 'analytics', route: '/analytics' },
    { id: 'signals', label: 'Signals', icon: 'notifications', route: '/signals' },
    {
      id: 'settings',
      label: 'Settings',
      icon: 'settings',
      active: false,
      children: [
        { id: 'account', label: 'Account', icon: 'account_circle', route: '/settings/account' },
        { id: 'preferences', label: 'Preferences', icon: 'tune', route: '/settings/preferences' },
        { id: 'notifications', label: 'Notifications', icon: 'notifications_active', route: '/settings/notifications' }
      ]
    }
  ];

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset).pipe(
    map(result => result.matches),
    takeUntil(this.destroy$),
    tap(isHandset => {
      if (isHandset) {
        this.isExpanded = false;
        this.collapseAll();
      }
    })
  );

  isExpanded: boolean = true;
  isAuthenticated$: Observable<boolean> = this.authService.authStatus$.pipe(map(s => s === AuthStatus.Authenticated));
  currentUser$: Observable<User | null> = this.authService.currentUser$;

  ngOnInit(): void {
    // Initialization logic if needed
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Toggle navigation expansion state
   */
  toggleNavigation(): void {
    this.isExpanded = !this.isExpanded;
    if (!this.isExpanded) {
      this.collapseAll();
    }
  }

  /**
   * Recursively collapse all navigation items.
   */
  collapseAll(items: NavItem[] = this.navItems): void {
    for (const item of items) {
      if (item.children) {
        item.active = false;
        this.collapseAll(item.children);
      }
    }
  }

  /**
   * Toggle submenu for a navigation item.
   * If the item has a route, navigate to it. Otherwise, just toggle the submenu.
   * @param item Navigation item
   * @param event Mouse event
   */
  toggleSubmenu(item: NavItem, event?: Event): void {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    if (item.children) {
      item.active = !item.active;
    }
  }

  /**
   * Logout user
   */
  logout(): void {
    this.authService.logout();
  }
}