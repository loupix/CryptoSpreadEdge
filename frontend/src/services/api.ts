import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Types pour les réponses API
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

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Intercepteur pour les erreurs
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async getHealth(): Promise<HealthResponse> {
    const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
    return response.data;
  }

  // Market Data
  async getMarketData(symbols: string[], timeframe: string = '1h', limit: number = 1000): Promise<MarketDataResponse[]> {
    const response: AxiosResponse<MarketDataResponse[]> = await this.client.post('/market-data/market-data', {
      symbols,
      timeframe,
      limit,
      include_indicators: false,
    });
    return response.data;
  }

  // Indicators
  async getIndicators(symbol: string, data: any[], indicators: string[]): Promise<IndicatorResponse> {
    const response: AxiosResponse<IndicatorResponse> = await this.client.post('/indicators/indicators', {
      symbol,
      data,
      indicators,
      timeframe: '1h',
    });
    return response.data;
  }

  async getAvailableIndicators(): Promise<{ indicators: string[]; count: number }> {
    const response = await this.client.get('/indicators/indicators/available');
    return response.data;
  }

  // Predictions
  async getPredictions(
    symbol: string,
    data: any[],
    modelType: string = 'ensemble',
    predictionHorizon: number = 5
  ): Promise<PredictionResponse> {
    const response: AxiosResponse<PredictionResponse> = await this.client.post('/predictions/predictions', {
      symbol,
      data,
      model_type: modelType,
      prediction_horizon: predictionHorizon,
      include_confidence: true,
    });
    return response.data;
  }

  async trainModels(
    symbol: string,
    data: any[],
    modelTypes: string[] = ['RandomForest', 'GradientBoosting', 'LSTM']
  ): Promise<any> {
    const response = await this.client.post('/predictions/training', {
      symbol,
      data,
      model_types: modelTypes,
      test_size: 0.2,
    });
    return response.data;
  }

  async getAvailableModels(): Promise<{ models: string[]; count: number }> {
    const response = await this.client.get('/predictions/models/available');
    return response.data;
  }

  // Metrics
  async getMetrics(): Promise<any> {
    const response = await this.client.get('/metrics');
    return response.data;
  }

  // Cache stats
  async getCacheStats(): Promise<any> {
    const response = await this.client.get('/market-data/cache/stats');
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;