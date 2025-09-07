// Types principaux pour l'application mobile CryptoSpreadEdge

export interface User {
  id: string;
  email: string;
  username: string;
  isAuthenticated: boolean;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  currency: string;
  language: string;
  notifications: NotificationSettings;
}

export interface NotificationSettings {
  priceAlerts: boolean;
  tradeAlerts: boolean;
  systemAlerts: boolean;
  pushEnabled: boolean;
}

export interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: string;
  platform: string;
}

export interface TradingPair {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  isActive: boolean;
  minTradeAmount: number;
  pricePrecision: number;
  quantityPrecision: number;
}

export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop';
  quantity: number;
  price?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
  timestamp: string;
  platform: string;
}

export interface Portfolio {
  totalValue: number;
  totalValueChange: number;
  totalValueChangePercent: number;
  positions: Position[];
  cash: number;
  lastUpdated: string;
}

export interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  value: number;
  pnl: number;
  pnlPercent: number;
  platform: string;
}

export interface ArbitrageOpportunity {
  id: string;
  symbol: string;
  buyPlatform: string;
  sellPlatform: string;
  buyPrice: number;
  sellPrice: number;
  spread: number;
  spreadPercent: number;
  profit: number;
  confidence: number;
  timestamp: string;
  isActive: boolean;
}

export interface IndicatorData {
  symbol: string;
  buyPlatform: string;
  sellPlatform: string;
  indicators: Record<string, number>;
  timestamp: string;
}

export interface ChartData {
  symbol: string;
  timeframe: string;
  data: ChartPoint[];
  indicators?: Record<string, ChartPoint[]>;
}

export interface ChartPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

export interface MarketDataRequest {
  symbols: string[];
  timeframe?: string;
  limit?: number;
  includeIndicators?: boolean;
}

export interface TradingRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  quantity: number;
  price?: number;
  platform: string;
}

export interface AlertRequest {
  symbol: string;
  condition: 'above' | 'below' | 'change';
  value: number;
  isActive: boolean;
}

export interface WebSocketMessage {
  type: 'market_data' | 'order_update' | 'portfolio_update' | 'arbitrage_opportunity';
  data: any;
  timestamp: string;
}

export interface NavigationProps {
  navigation: any;
  route: any;
}

export interface ScreenProps extends NavigationProps {
  // Props communes à tous les écrans
}

export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  typography: {
    h1: object;
    h2: object;
    h3: object;
    body: object;
    caption: object;
  };
}