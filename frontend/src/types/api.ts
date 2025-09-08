// Types API (REST gateway)

export interface MarketDataResponse {
  symbol: string;
  data: Array<{
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    source: string;
  }>;
  timestamp: string;
  source: string;
  cached: boolean;
}

export interface IndicatorResponse {
  symbol: string;
  indicators: Record<string, Array<{
    value: number;
    timestamp: string;
    confidence: number;
    metadata: Record<string, any>;
  }>>;
  timestamp: string;
  processing_time: number;
  cached: boolean;
}

export interface PredictionResponse {
  symbol: string;
  predictions: Array<{
    predicted_price: number;
    predicted_change: number;
    confidence: number;
    timestamp: string;
    model_name: string;
    features_used: string[];
    metadata: Record<string, any>;
  }>;
  model_used: string;
  timestamp: string;
  processing_time: number;
  confidence: number;
  cached: boolean;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  services: Record<string, {
    name: string;
    status: string;
    response_time: number;
    last_check: string;
    endpoint: string;
  }>;
  total_requests: number;
  error_rate: number;
}

