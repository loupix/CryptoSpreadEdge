// Types domaine centralisés pour le frontend

export interface Exchange {
  id: string;
  name: string;
  display_name?: string;
  exchange_type?: 'centralized' | 'decentralized' | 'hybrid';
  status: 'active' | 'inactive' | 'maintenance' | 'suspended' | 'error' | 'inactive';
  api_base_url?: string;
  websocket_url?: string;
  supported_pairs?: string[];
  trading_fees?: { maker: number; taker: number };
  withdrawal_fees?: Record<string, number>;
  limits?: Record<string, any>;
  features?: string[];
  countries?: string[];
  is_regulated?: boolean;
  regulation_authorities?: string[];
  kyc_required?: boolean;
  created_at?: string;
  updated_at?: string;
  latency_ms?: number;
}

export interface Order {
  id: string;
  order_id?: string;
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop' | 'stop_limit' | string;
  quantity: number;
  price?: number;
  stop_price?: number;
  status: 'pending' | 'open' | 'filled' | 'partially_filled' | 'canceled' | 'rejected' | 'open';
  filled_quantity?: number;
  average_price?: number;
  exchange?: string;
  source?: string;
  created_at?: string;
  updated_at?: string;
  filled_at?: string;
  cancelled_at?: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short' | 'buy' | 'sell';
  quantity: number;
  entry_price?: number | null;
  average_price?: number | null;
  current_price?: number | null;
  unrealized_pnl?: number | null;
  realized_pnl?: number | null;
  status?: 'open' | 'closed' | 'partially_closed' | string;
  exchange?: string | null;
  strategy_id?: string | null;
  opened_at?: string | number | Date | null;
  closed_at?: string | number | Date | null;
  updated_at?: string | number | Date | null;
}

export interface Trade {
  id: string;
  trade_id?: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  fees?: number;
  pnl?: number;
  net_pnl?: number;
  order_id?: string;
  position_id?: string;
  strategy_id?: string;
  exchange?: string;
  executed_at?: string;
  signal_strength?: number;
  signal_confidence?: number;
  exit_reason?: string;
  timestamp?: string | number | Date;
}

export interface Portfolio {
  id: string;
  user_id?: string;
  trading_session_id?: string;
  total_value: number;
  cash_balance: number;
  invested_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_fees?: number;
  active_positions: number;
  total_trades: number;
  winning_trades?: number;
  losing_trades?: number;
  win_rate?: number;
  max_drawdown?: number;
  sharpe_ratio?: number;
  timestamp: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'trader' | 'viewer' | 'analyst' | 'auditor';
  status: 'active' | 'inactive' | 'suspended' | 'pending_verification';
  first_name?: string;
  last_name?: string;
  phone?: string;
  timezone?: string;
  language?: string;
  last_login?: string;
  login_count: number;
  email_verified?: boolean;
  phone_verified?: boolean;
  two_factor_enabled?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AlertType {
  id: string;
  user_id: string;
  name: string;
  alert_type: 'price' | 'volume' | 'risk' | 'system' | 'trading' | 'performance';
  severity: 'low' | 'medium' | 'high' | 'critical';
  symbol?: string;
  condition: Record<string, unknown>;
  is_active: boolean;
  triggered_count: number;
  last_triggered?: string;
  cooldown_seconds?: number;
  created_at: string | number | Date;
  updated_at?: string;
}

export interface Notification {
  id: string;
  user_id?: string;
  alert_id?: string;
  channel?: 'email' | 'sms' | 'slack' | 'discord' | 'webhook' | 'push';
  title?: string;
  message?: string;
  is_sent?: boolean;
  sent_at?: string;
  retry_count?: number;
  max_retries?: number;
  error_message?: string;
  created_at?: string;
}

export interface LatencyItem {
  name: string;
  status: string;
  response_time: number;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  time: string;
}