export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user: User;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

export interface TokenPayload {
  sub: string; // user id
  username: string;
  role: string;
  permissions: string[];
  iat: number; // issued at
  exp: number; // expiration
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
  confirm_password: string;
}

export enum AuthStatus {
  Initializing = 'INITIALIZING',
  Authenticated = 'AUTHENTICATED',
  NotAuthenticated = 'NOT_AUTHENTICATED',
  TokenExpired = 'TOKEN_EXPIRED',
  Refreshing = 'REFRESHING',
  Error = 'ERROR'
}

export enum UserRole {
  Admin = 'admin',
  Trader = 'trader',
  Viewer = 'viewer'
}

export enum Permission {
  ReadSignals = 'read_signals',
  WriteSignals = 'write_signals',
  ReadTrades = 'read_trades',
  WriteTrades = 'write_trades',
  ReadAccount = 'read_account',
  WriteAccount = 'write_account',
  ReadAnalytics = 'read_analytics',
  WriteConfig = 'write_config',
  AdminAccess = 'admin_access'
}