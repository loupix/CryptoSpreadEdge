/**
 * Service API pour l'intégration avec la base de données PostgreSQL
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Configuration axios
const databaseApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification
databaseApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour gérer les erreurs
databaseApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types TypeScript
export interface Order {
  id: string;
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price?: number;
  stop_price?: number;
  status: 'pending' | 'open' | 'filled' | 'partially_filled' | 'canceled' | 'rejected';
  filled_quantity: number;
  average_price: number;
  exchange: string;
  source: string;
  created_at: string;
  updated_at: string;
  filled_at?: string;
  cancelled_at?: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  average_price: number;
  current_price?: number;
  unrealized_pnl: number;
  realized_pnl: number;
  status: 'open' | 'closed' | 'partially_closed';
  exchange: string;
  strategy_id?: string;
  opened_at: string;
  closed_at?: string;
  updated_at: string;
}

export interface Trade {
  id: string;
  trade_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  fees: number;
  pnl: number;
  net_pnl: number;
  order_id?: string;
  position_id?: string;
  strategy_id?: string;
  exchange: string;
  executed_at: string;
  signal_strength?: number;
  signal_confidence?: number;
  exit_reason?: string;
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
  total_fees: number;
  active_positions: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio: number;
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
  timezone: string;
  language: string;
  last_login?: string;
  login_count: number;
  email_verified: boolean;
  phone_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Exchange {
  id: string;
  name: string;
  display_name: string;
  exchange_type: 'centralized' | 'decentralized' | 'hybrid';
  status: 'active' | 'inactive' | 'maintenance' | 'suspended' | 'error';
  api_base_url: string;
  websocket_url?: string;
  supported_pairs: string[];
  trading_fees: {
    maker: number;
    taker: number;
  };
  withdrawal_fees: Record<string, number>;
  limits: Record<string, any>;
  features: string[];
  countries: string[];
  is_regulated: boolean;
  regulation_authorities: string[];
  kyc_required: boolean;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  user_id: string;
  name: string;
  alert_type: 'price' | 'volume' | 'risk' | 'system' | 'trading' | 'performance';
  severity: 'low' | 'medium' | 'high' | 'critical';
  symbol?: string;
  condition: Record<string, any>;
  is_active: boolean;
  triggered_count: number;
  last_triggered?: string;
  cooldown_seconds: number;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  alert_id?: string;
  channel: 'email' | 'sms' | 'slack' | 'discord' | 'webhook' | 'push';
  title: string;
  message: string;
  is_sent: boolean;
  sent_at?: string;
  retry_count: number;
  max_retries: number;
  error_message?: string;
  created_at: string;
}

// API Methods
export const databaseApiService = {
  // Health Check
  async getHealth() {
    const response = await databaseApi.get('/historical/health');
    return response.data;
  },

  // Orders
  async getOrders(params?: {
    symbol?: string;
    status?: string;
    exchange?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await databaseApi.get('/historical/orders', { params });
    return response.data;
  },

  async getOrderById(id: string) {
    const response = await databaseApi.get(`/historical/orders/${id}`);
    return response.data;
  },

  async createOrder(orderData: Partial<Order>) {
    const response = await databaseApi.post('/historical/orders', orderData);
    return response.data;
  },

  async updateOrder(id: string, orderData: Partial<Order>) {
    const response = await databaseApi.put(`/historical/orders/${id}`, orderData);
    return response.data;
  },

  async deleteOrder(id: string) {
    const response = await databaseApi.delete(`/historical/orders/${id}`);
    return response.data;
  },

  // Positions
  async getPositions(params?: {
    symbol?: string;
    status?: string;
    exchange?: string;
    strategy_id?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await databaseApi.get('/historical/positions', { params });
    return response.data;
  },

  async getPositionById(id: string) {
    const response = await databaseApi.get(`/historical/positions/${id}`);
    return response.data;
  },

  async createPosition(positionData: Partial<Position>) {
    const response = await databaseApi.post('/historical/positions', positionData);
    return response.data;
  },

  async updatePosition(id: string, positionData: Partial<Position>) {
    const response = await databaseApi.put(`/historical/positions/${id}`, positionData);
    return response.data;
  },

  async closePosition(id: string) {
    const response = await databaseApi.post(`/historical/positions/${id}/close`);
    return response.data;
  },

  // Trades
  async getTrades(params?: {
    symbol?: string;
    exchange?: string;
    strategy_id?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await databaseApi.get('/historical/trades', { params });
    return response.data;
  },

  async getTradeById(id: string) {
    const response = await databaseApi.get(`/historical/trades/${id}`);
    return response.data;
  },

  async getTradesSummary(params?: {
    start_date?: string;
    end_date?: string;
    symbol?: string;
    exchange?: string;
  }) {
    const response = await databaseApi.get('/historical/trades/summary', { params });
    return response.data;
  },

  // Portfolio
  async getPortfolioHistory(params?: {
    user_id?: string;
    trading_session_id?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) {
    const response = await databaseApi.get('/historical/portfolio', { params });
    return response.data;
  },

  async getPortfolioSummary(params?: {
    user_id?: string;
    trading_session_id?: string;
  }) {
    const response = await databaseApi.get('/historical/portfolio/summary', { params });
    return response.data;
  },

  // Users
  async getUsers(params?: {
    role?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await databaseApi.get('/users', { params });
    return response.data;
  },

  async getUserById(id: string) {
    const response = await databaseApi.get(`/users/${id}`);
    return response.data;
  },

  async createUser(userData: Partial<User>) {
    const response = await databaseApi.post('/users', userData);
    return response.data;
  },

  async updateUser(id: string, userData: Partial<User>) {
    const response = await databaseApi.put(`/users/${id}`, userData);
    return response.data;
  },

  async deleteUser(id: string) {
    const response = await databaseApi.delete(`/users/${id}`);
    return response.data;
  },

  // Exchanges
  async getExchanges(params?: {
    status?: string;
    exchange_type?: string;
    country?: string;
    feature?: string;
  }) {
    const response = await databaseApi.get('/exchanges', { params });
    return response.data;
  },

  async getExchangeById(id: string) {
    const response = await databaseApi.get(`/exchanges/${id}`);
    return response.data;
  },

  // Alerts
  async getAlerts(params?: {
    user_id?: string;
    alert_type?: string;
    severity?: string;
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const response = await databaseApi.get('/alerts', { params });
    return response.data;
  },

  async getAlertById(id: string) {
    const response = await databaseApi.get(`/alerts/${id}`);
    return response.data;
  },

  async createAlert(alertData: Partial<Alert>) {
    const response = await databaseApi.post('/alerts', alertData);
    return response.data;
  },

  async updateAlert(id: string, alertData: Partial<Alert>) {
    const response = await databaseApi.put(`/alerts/${id}`, alertData);
    return response.data;
  },

  async deleteAlert(id: string) {
    const response = await databaseApi.delete(`/alerts/${id}`);
    return response.data;
  },

  // Notifications
  async getNotifications(params?: {
    user_id?: string;
    channel?: string;
    is_sent?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const response = await databaseApi.get('/notifications', { params });
    return response.data;
  },

  async getNotificationById(id: string) {
    const response = await databaseApi.get(`/notifications/${id}`);
    return response.data;
  },

  async markNotificationAsRead(id: string) {
    const response = await databaseApi.post(`/notifications/${id}/read`);
    return response.data;
  },

  // Performance Metrics
  async getPerformanceMetrics(params?: {
    metric_name?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) {
    const response = await databaseApi.get('/performance/metrics', { params });
    return response.data;
  },

  async getPerformanceSummary() {
    const response = await databaseApi.get('/performance/summary');
    return response.data;
  },

  // Security Events
  async getSecurityEvents(params?: {
    user_id?: string;
    severity?: string;
    action?: string;
    limit?: number;
    offset?: number;
  }) {
    const response = await databaseApi.get('/security/events', { params });
    return response.data;
  },

  async getSecuritySummary() {
    const response = await databaseApi.get('/security/summary');
    return response.data;
  },

  // Backup Status
  async getBackupStatus() {
    const response = await databaseApi.get('/backup/status');
    return response.data;
  },

  async getBackupList(params?: {
    config_name?: string;
    limit?: number;
  }) {
    const response = await databaseApi.get('/backup/list', { params });
    return response.data;
  },

  async executeBackup(configName: string) {
    const response = await databaseApi.post(`/backup/execute/${configName}`);
    return response.data;
  },
};

export default databaseApiService;