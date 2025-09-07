// Service API principal pour l'application mobile
import AsyncStorage from '@react-native-async-storage/async-storage';
import { 
  ApiResponse, 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  User, 
  MarketData, 
  MarketDataRequest,
  TradingRequest,
  Order,
  Portfolio,
  ArbitrageOpportunity,
  IndicatorData,
  AlertRequest
} from '../types';

const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000/api' 
  : 'https://api.cryptospreadedge.com/api';

class ApiService {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.initializeToken();
  }

  private async initializeToken() {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      this.token = token;
    } catch (error) {
      console.error('Erreur lors de la récupération du token:', error);
    }
  }

  private async getHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = await this.getHeaders();

      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.message || 'Erreur de requête',
        };
      }

      return {
        success: true,
        data: data,
      };
    } catch (error) {
      console.error('Erreur API:', error);
      return {
        success: false,
        error: 'Erreur de connexion',
      };
    }
  }

  // Authentification
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (response.success && response.data) {
      this.token = response.data.token;
      await AsyncStorage.setItem('auth_token', response.data.token);
      await AsyncStorage.setItem('refresh_token', response.data.refreshToken);
    }

    return response;
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<LoginResponse>> {
    return this.request<LoginResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async logout(): Promise<ApiResponse<void>> {
    const response = await this.request<void>('/auth/logout', {
      method: 'POST',
    });

    if (response.success) {
      this.token = null;
      await AsyncStorage.removeItem('auth_token');
      await AsyncStorage.removeItem('refresh_token');
    }

    return response;
  }

  async refreshToken(): Promise<ApiResponse<LoginResponse>> {
    try {
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      if (!refreshToken) {
        return { success: false, error: 'Aucun refresh token disponible' };
      }

      const response = await this.request<LoginResponse>('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refreshToken }),
      });

      if (response.success && response.data) {
        this.token = response.data.token;
        await AsyncStorage.setItem('auth_token', response.data.token);
        await AsyncStorage.setItem('refresh_token', response.data.refreshToken);
      }

      return response;
    } catch (error) {
      return { success: false, error: 'Erreur lors du refresh du token' };
    }
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/me');
  }

  // Données de marché
  async getMarketData(request: MarketDataRequest): Promise<ApiResponse<MarketData[]>> {
    const params = new URLSearchParams();
    params.append('symbols', request.symbols.join(','));
    if (request.timeframe) params.append('timeframe', request.timeframe);
    if (request.limit) params.append('limit', request.limit.toString());
    if (request.includeIndicators) params.append('includeIndicators', 'true');

    return this.request<MarketData[]>(`/market/data?${params.toString()}`);
  }

  async getTradingPairs(): Promise<ApiResponse<string[]>> {
    return this.request<string[]>('/market/pairs');
  }

  async getIndicators(symbol: string, buyPlatform: string, sellPlatform: string): Promise<ApiResponse<IndicatorData>> {
    const params = new URLSearchParams();
    params.append('symbol', symbol);
    params.append('buy_platform', buyPlatform);
    params.append('sell_platform', sellPlatform);

    return this.request<IndicatorData>(`/indicators/bundle?${params.toString()}`);
  }

  // Trading
  async placeOrder(order: TradingRequest): Promise<ApiResponse<Order>> {
    return this.request<Order>('/trading/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  }

  async getOrders(symbol?: string): Promise<ApiResponse<Order[]>> {
    const params = symbol ? `?symbol=${symbol}` : '';
    return this.request<Order[]>(`/trading/orders${params}`);
  }

  async cancelOrder(orderId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/trading/orders/${orderId}`, {
      method: 'DELETE',
    });
  }

  // Portefeuille
  async getPortfolio(): Promise<ApiResponse<Portfolio>> {
    return this.request<Portfolio>('/portfolio');
  }

  async getPositions(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/portfolio/positions');
  }

  // Arbitrage
  async getArbitrageOpportunities(): Promise<ApiResponse<ArbitrageOpportunity[]>> {
    return this.request<ArbitrageOpportunity[]>('/arbitrage/opportunities');
  }

  async getArbitrageHistory(): Promise<ApiResponse<ArbitrageOpportunity[]>> {
    return this.request<ArbitrageOpportunity[]>('/arbitrage/history');
  }

  // Alertes
  async createAlert(alert: AlertRequest): Promise<ApiResponse<any>> {
    return this.request<any>('/alerts', {
      method: 'POST',
      body: JSON.stringify(alert),
    });
  }

  async getAlerts(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/alerts');
  }

  async updateAlert(alertId: string, alert: Partial<AlertRequest>): Promise<ApiResponse<any>> {
    return this.request<any>(`/alerts/${alertId}`, {
      method: 'PUT',
      body: JSON.stringify(alert),
    });
  }

  async deleteAlert(alertId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/alerts/${alertId}`, {
      method: 'DELETE',
    });
  }

  // Configuration
  async updateUserPreferences(preferences: Partial<any>): Promise<ApiResponse<User>> {
    return this.request<User>('/user/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  // Santé de l'API
  async healthCheck(): Promise<ApiResponse<any>> {
    return this.request<any>('/health');
  }
}

export const apiService = new ApiService();
export default apiService;