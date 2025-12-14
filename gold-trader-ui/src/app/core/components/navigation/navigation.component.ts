import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ViewChild, ElementRef } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { takeUntil, filter, map, tap } from 'rxjs/operators';
import { AuthService } from '@core/services/auth.service';
import { WebSocketService } from '@core/services/websocket.service';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';

interface NavItem {
  id: string;
  label: string;
  icon: string;
  route?: string;
  children?: NavItem[];
  active?: boolean;
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
  @ViewChild('navContainer') navContainer!: ElementRef;

  private destroy$ = new Subject<void>();
  private currentUrl: string = '';

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
      children: [
        {
          id: 'charts',
          label: 'Charts',
          icon: 'show_chart',
          route: '/trading/charts'
        },
        {
          id: 'orders',
          label: 'Orders',
          icon: 'receipt_long',
          route: '/trading/orders'
        },
        {
          id: 'history',
          label: 'History',
          icon: 'history',
          route: '/trading/history'
        }
      ]
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: 'analytics',
      route: '/analytics'
    },
    {
      id: 'signals',
      label: 'Signals',
      icon: 'notifications',
      route: '/signals'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: 'settings',
      children: [
        {
          id: 'account',
          label: 'Account',
          icon: 'account_circle',
          route: '/settings/account'
        },
        {
          id: 'preferences',
          label: 'Preferences',
          icon: 'tune',
          route: '/settings/preferences'
        },
        {
          id: 'notifications',
          label: 'Notifications',
          icon: 'notifications_active',
          route: '/settings/notifications'
        }
      ]
    }
  ];

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset).pipe(
    map(result => result.matches),
    takeUntil(this.destroy$),
    tap(result => {
      if (result) {
        this.collapseAll();
      }
    })
  );

  isExpanded: boolean = true;
  isAuthenticated: boolean = false;
  currentUsername: string = 'User';

  constructor(
    private router: Router,
    public authService: AuthService,
    private webSocketService: WebSocketService,
    private breakpointObserver: BreakpointObserver
  ) {}

  ngOnInit(): void {
    // Set initial active item based on current route
    this.router.events.pipe(
      takeUntil(this.destroy$),
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: NavigationEnd) => {
      this.currentUrl = event.urlAfterRedirects;
      this.setActiveItem();
    });

    // Subscribe to auth status
    this.authService.authStatus$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(status => {
      this.isAuthenticated = status === 'AUTHENTICATED';
    });

    // Subscribe to current user
    this.authService.currentUser$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(user => {
      this.currentUsername = user?.username || 'User';
    });

    // Set initial active item
    this.setActiveItem();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Set active navigation item based on current route
   */
  setActiveItem(): void {
    this.navItems.forEach(item => {
      this.setItemActive(item);
    });
  }

  /**
   * Recursively set item active state
   * @param item Navigation item
   */
  setItemActive(item: NavItem): void {
    if (item.route && this.currentUrl.includes(item.route)) {
      item.active = true;
    } else {
      item.active = false;
    }

    if (item.children) {
      item.children.forEach(child => {
        this.setItemActive(child);
      });
    }
  }

  /**
   * Toggle navigation expansion state
   */
  toggleNavigation(): void {
    this.isExpanded = !this.isExpanded;
    // Collapse all items when navigation is collapsed
    if (!this.isExpanded) {
      this.collapseAll();
    }
  }

  /**
   * Collapse all navigation items
   */
  collapseAll(): void {
    this.navItems.forEach(item => {
      if (item.children) {
        item.active = false;
      }
    });
  }

  /**
   * Toggle submenu for a navigation item
   * @param item Navigation item
   * @param event Mouse event
   */
  toggleSubmenu(item: NavItem, event: Event): void {
    event.preventDefault();
    event.stopPropagation();

    if (item.children) {
      item.active = !item.active;
    } else if (item.route) {
      this.router.navigate([item.route]);
    }
  }

  /**
   * Navigate to a route
   * @param item Navigation item
   * @param event Mouse event
   */
  navigateTo(item: NavItem, event: Event): void {
    event.preventDefault();
    event.stopPropagation();

    if (item.route) {
      this.router.navigate([item.route]);
    }
  }

  /**
   * Logout user
   */
  logout(): void {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }

  /**
   * Check if an item has active children
   * @param item Navigation item
   * @returns boolean
   */
  hasActiveChildren(item: NavItem): boolean {
    if (!item.children) return false;
    return item.children.some(child => child.active || this.hasActiveChildren(child));
  }

  /**
   * Check if an item is active
   * @param item Navigation item
   * @returns boolean
   */
  isItemActive(item: NavItem): boolean {
    if (item.route && this.currentUrl.includes(item.route)) {
      return true;
    }
    if (item.children) {
      return item.children.some(child => this.isItemActive(child));
    }
    return false;
  }
}