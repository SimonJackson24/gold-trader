# Gold Trader UI - Fix Implementation Plan

This plan outlines the steps to address the issues identified in the "Gold Trader UI - Comprehensive Analysis Report." The fixes are prioritized and grouped for efficient implementation.

## Phase 1: Critical Fixes & Stability Improvements (High-Priority Issues)

These fixes are essential for the application's stability and correct functioning.

### 1. Refactor Token Refresh Logic in AuthService

- **Objective:** Consolidate and correct the token refresh mechanism to ensure reliable session management.
- **Steps:**
    1.  Remove the `setupTokenRefresh()` method entirely.
    2.  Modify `scheduleTokenRefresh()` to be the sole mechanism for scheduling token refreshes, ensuring it correctly calculates the refresh time before expiration.
    3.  Ensure `scheduleTokenRefresh()` is called after successful login and after a successful token refresh.
    4.  Update the `initializeAuthFromStorage()` method to gracefully handle an expired token by initiating a refresh and waiting for its completion before signaling `AuthStatus.Authenticated` to prevent race conditions during app startup.
    5.  Ensure proper cleanup of `refreshTimer` and `refreshSubscription` on logout and component destruction.

### 2. Refactor WebSocket Reconnection Logic

- **Objective:** Simplify and centralize the WebSocket reconnection logic using RxJS operators for robustness.
- **Steps:**
    1.  Remove the manual reconnection logic from the `handleClose()` method.
    2.  Configure the `retry` operator in `setupMessageHandling()` to manage all reconnection attempts, including delays and maximum attempts, using `environment.wsReconnectInterval` and `environment.wsMaxReconnectAttempts`.
    3.  Ensure `createWebSocket()` returns a `WebSocketSubject` or throws an error, rather than returning `any`.
    4.  Implement a more granular connection status (`CONNECTING`, `CONNECTED`, `RECONNECTING`, `DISCONNECTED`) using a `BehaviorSubject` to provide better UI feedback.

### 3. Update UI to Reflect True Connection Status

- **Objective:** Display the actual WebSocket connection status in the `AppComponent`'s toolbar.
- **Steps:**
    1.  Inject `WebSocketService` into `AppComponent`.
    2.  Subscribe to the `WebSocketService`'s connection status observable.
    3.  Update the `AppComponent`'s template to dynamically display the connection status (e.g., "Connected", "Connecting...", "Disconnected") based on the service's observable.

## Phase 2: Best Practices & Code Modernization (Medium-Priority Issues)

These fixes improve code quality, maintainability, and align with modern Angular practices.

### 1. Migrate from TSLint to ESLint

- **Objective:** Update the project's linting configuration to use ESLint, the current standard for Angular.
- **Steps:**
    1.  Install `@angular-eslint/schematics` and other necessary ESLint packages.
    2.  Run the Angular ESLint migration schematic (`ng add @angular-eslint/schematics`).
    3.  Review and adjust generated ESLint configuration files (`.eslintrc.json`) as needed.
    4.  Remove TSLint-related dependencies and configurations from `package.json` and `angular.json`.

### 2. Refactor Navigation Component to Use `routerLinkActive`

- **Objective:** Simplify the `NavigationComponent`'s active link detection.
- **Steps:**
    1.  Remove manual active state tracking properties and methods (`isItemActive`, `setActiveItem`, `hasActiveChildren`, `navigateTo`) from `navigation.component.ts`.
    2.  Update `navigation.component.html` to use `routerLink` and `routerLinkActive="active"` with `[routerLinkActiveOptions]="{exact: true}"` for all navigation links.
    3.  Adjust `toggleSubmenu` logic if necessary to integrate cleanly with `routerLink`.

### 3. Modernize Angular Material Imports

- **Objective:** Replace the `MaterialModule` with direct imports of standalone Material components.
- **Steps:**
    1.  Identify all Angular Material components used within `MaterialModule`.
    2.  For each component that imports `MaterialModule`, import the specific standalone Material components it needs directly into its `imports` array.
    3.  Once no components are importing `MaterialModule`, delete `src/app/shared/material.module.ts`. This can be done incrementally or as a single large refactoring.

### 4. Update Outdated NPM Dependencies

- **Objective:** Bring project dependencies up to date.
- **Steps:**
    1.  Run `npm outdated` to get a list of all outdated packages.
    2.  Carefully update major version dependencies (e.g., `date-fns` v2 to v3), reviewing their changelogs for breaking changes and adapting the code as necessary.
    3.  Update minor and patch version dependencies.
    4.  Test the application thoroughly after each significant dependency update.

## Phase 3: Code Cleanliness & Minor Improvements (Low-Priority Issues)

These improvements enhance the overall quality and readability of the codebase.

### 1. Remove Unused Navigation Module

- **Objective:** Delete dead code.
- **Steps:**
    1.  Delete `src/app/core/components/navigation/navigation.module.ts`.

### 2. Standardize Timer Implementation in AuthService

- **Objective:** Use a consistent approach for scheduling in `AuthService`.
- **Steps:**
    1.  Replace `setTimeout` with RxJS `timer` where appropriate in the token refresh logic (after refactoring token refresh in Phase 1).

### 3. Simplify `sendMessage` in WebSocketService

- **Objective:** Remove unnecessary Observable wrapper.
- **Steps:**
    1.  Modify the `sendMessage` method to return `void` or a simpler boolean/status indicator, removing the `new Observable` wrapper.
    2.  Ensure consumers of `sendMessage` adapt to the new return type.

## Next Steps

After approval of this plan, I will proceed with implementing the fixes in the order outlined above, starting with Phase 1. Each change will be accompanied by appropriate testing to ensure stability and correctness.
