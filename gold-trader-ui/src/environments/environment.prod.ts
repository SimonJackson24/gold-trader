// Copyright (c) 2024 Simon Callaghan. All rights reserved.

export const environment = {
  production: true,
  apiUrl: 'https://api.yourdomain.com/api/v1',
  wsUrl: 'wss://api.yourdomain.com/ws',
  wsReconnectInterval: 5000,
  wsMaxReconnectAttempts: 10,
  chartUpdateInterval: 1000,
  priceUpdateInterval: 500,
  signalTimeout: 30000,
  defaultChartTimeframe: 'M15',
  maxChartPoints: 1000,
  enableDebugMode: false,
  enableMockData: false,
  mockDataDelay: 1000,
  sessionTimeout: 3600000, // 1 hour in milliseconds
  tokenRefreshThreshold: 300000, // 5 minutes in milliseconds
  enableAnalytics: true,
  enablePerformanceMonitoring: true,
  defaultRiskPercentage: 1.0,
  maxConcurrentTrades: 2,
  minRiskRewardRatio: 2.0,
  defaultStopLossPips: 50,
  defaultTakeProfitPips: 100,
  enableSoundAlerts: true,
  enablePushNotifications: true,
  enableEmailNotifications: false,
  timezone: 'UTC',
  dateFormat: 'yyyy-MM-dd HH:mm:ss',
  numberFormat: 'en-US',
  currency: 'USD',
  theme: 'default',
  language: 'en'
};