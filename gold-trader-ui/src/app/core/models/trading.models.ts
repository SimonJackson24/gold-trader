export interface PriceTick {
  symbol: string;
  timestamp: string;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  spread: number;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timeframe: string;
}

export interface TradingSignal {
  signal_id: string;
  instrument: string;
  direction: 'BUY' | 'SELL';
  entry_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  risk_reward_ratio: number;
  position_size: number;
  risk_percentage: number;
  setup_type: string;
  market_structure: string;
  confluence_factors: string[];
  confidence_score: number;
  h4_context: string;
  h1_context: string;
  m15_context: string;
  session: 'ASIAN' | 'LONDON' | 'NY_OVERLAP';
  created_at: string;
  updated_at: string;
  status: 'ACTIVE' | 'EXECUTED' | 'CANCELLED' | 'EXPIRED';
  telegram_message_id?: number;
  trade?: Trade;
}

export interface Trade {
  trade_id: string;
  signal_id: string;
  entry_time: string;
  exit_time?: string;
  entry_price: number;
  exit_price?: number;
  highest_price?: number;
  lowest_price?: number;
  profit_loss: number;
  profit_loss_pips: number;
  profit_loss_percentage: number;
  position_size: number;
  status: 'PENDING' | 'OPEN' | 'CLOSED' | 'CANCELLED';
  partial_closes: PartialClose[];
  tp1_hit: boolean;
  tp2_hit: boolean;
  breakeven_moved: boolean;
  exit_reason?: 'TP1_HIT' | 'TP2_HIT' | 'SL_HIT' | 'MANUAL_CLOSE' | 'EXPIRED';
  duration_minutes?: number;
}

export interface PartialClose {
  time: string;
  price: number;
  size: number;
  profit: number;
}

export interface AccountInfo {
  balance: number;
  equity: number;
  margin: number;
  margin_free: number;
  margin_level: number;
  profit: number;
  open_trades: number;
  closed_trades: number;
  total_volume: number;
  deposit: number;
  withdrawal: number;
}

export interface Position {
  ticket: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  volume: number;
  price_open: number;
  price_current: number;
  sl: number;
  tp: number;
  swap: number;
  profit: number;
  time: string;
  comment: string;
}

export interface TradeUpdate {
  trade_id: string;
  status: string;
  current_price?: number;
  profit_loss?: number;
  profit_loss_pips?: number;
  exit_reason?: string;
  timestamp: string;
}

export interface AccountUpdate {
  balance: number;
  equity: number;
  margin: number;
  margin_free: number;
  profit: number;
  open_trades: number;
  timestamp: string;
}

// Smart Money Concepts Models
export interface FairValueGap {
  id: string;
  type: 'BULLISH' | 'BEARISH';
  top_price: number;
  bottom_price: number;
  start_time: string;
  end_time: string;
  strength: number;
  is_active: boolean;
  timeframe: string;
}

export interface OrderBlock {
  id: string;
  type: 'BULLISH' | 'BEARISH';
  price: number;
  range_size: number;
  volume: number;
  start_time: string;
  end_time: string;
  strength: number;
  is_rejection_candle: boolean;
  wick_ratio: number;
  is_active: boolean;
  timeframe: string;
}

export interface LiquidityPool {
  id: string;
  price: number;
  strength: number;
  pool_type: 'BUY_SIDE' | 'SELL_SIDE';
  created_at: string;
  touched_count: number;
  last_touched?: string;
  is_swept: boolean;
  timeframe: string;
}

export interface LiquiditySweep {
  id: string;
  sweep_type: 'BUY_SIDE' | 'SELL_SIDE';
  pool_price: number;
  sweep_price: number;
  extension_pips: number;
  reversal_strength: number;
  start_time: string;
  end_time: string;
  confidence: number;
  timeframe: string;
}

export interface MarketStructure {
  id: string;
  type: 'BOS' | 'CHoCH';
  direction: 'BULLISH' | 'BEARISH';
  price: number;
  timestamp: string;
  strength: number;
  timeframe: string;
}

export interface PerformanceMetrics {
  date: string;
  instrument: string;
  total_signals: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  average_rr: number;
  total_pips: number;
  total_profit_loss: number;
  largest_win: number;
  largest_loss: number;
  max_drawdown: number;
  sharpe_ratio: number;
}

export interface SignalQueryParams {
  instrument?: string;
  limit?: number;
  offset?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export interface TradeQueryParams {
  instrument?: string;
  limit?: number;
  offset?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartConfig {
  type: 'candlestick' | 'line' | 'area';
  timeframe: string;
  showVolume: boolean;
  showGrid: boolean;
  showCrosshair: boolean;
  autoScale: boolean;
  backgroundColor: string;
  gridColor: string;
  upColor: string;
  downColor: string;
  volumeColor: string;
}

export interface ChartOverlay {
  id: string;
  type: 'fvg' | 'orderBlock' | 'liquidity' | 'structure' | 'trendline';
  data: any;
  visible: boolean;
  color: string;
  opacity: number;
  label?: string;
}

export interface ChartPoint {
  x: number; // timestamp
  y: number; // price
  volume?: number;
}

// Chart Library Specific Models
export interface DrawingTool {
  id: string;
  type: 'trendline' | 'horizontal' | 'vertical' | 'rectangle' | 'fibonacci';
  startPoint: { x: number; y: number };
  endPoint: { x: number; y: number };
  color: string;
  width: number;
  style: 'solid' | 'dashed' | 'dotted';
  label?: string;
}

export interface TechnicalIndicator {
  id: string;
  name: string;
  type: 'MA' | 'RSI' | 'MACD' | 'BB' | 'STOCH';
  parameters: Record<string, any>;
  visible: boolean;
  color: string;
  style: 'line' | 'area' | 'histogram';
}

export enum Timeframe {
  M1 = 'M1',
  M5 = 'M5',
  M15 = 'M15',
  M30 = 'M30',
  H1 = 'H1',
  H4 = 'H4',
  D1 = 'D1',
  W1 = 'W1',
  MN1 = 'MN1'
}

export enum TradingSession {
  Asian = 'ASIAN',
  London = 'LONDON',
  NewYork = 'NEW_YORK',
  LondonNewYork = 'LONDON_NY_OVERLAP',
  AsianLondon = 'ASIAN_LONDON_OVERLAP'
}

export enum SignalStatus {
  Active = 'ACTIVE',
  Executed = 'EXECUTED',
  Cancelled = 'CANCELLED',
  Expired = 'EXPIRED'
}

export enum TradeStatus {
  Pending = 'PENDING',
  Open = 'OPEN',
  Closed = 'CLOSED',
  Cancelled = 'CANCELLED'
}

export enum Direction {
  Buy = 'BUY',
  Sell = 'SELL'
}

// Response interfaces for API calls
export interface SignalResponse {
  signals: TradingSignal[];
  total: number;
  limit: number;
  offset: number;
}

export interface TradeResponse {
  trades: Trade[];
  total: number;
  limit: number;
  offset: number;
}

export interface AccountResponse {
  account: AccountInfo;
}

export interface PerformanceResponse {
  metrics: PerformanceMetrics[];
  summary: {
    total_days: number;
    average_win_rate: number;
    total_profit_loss: number;
    total_pips: number;
  };
}