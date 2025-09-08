// Types orientés DB / Backend DTOs

export interface UserDTO {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: 'admin' | 'trader' | 'analyst' | 'viewer' | 'auditor' | string;
  status: 'active' | 'inactive' | 'suspended' | 'pending_verification' | string;
  email_verified?: boolean;
  phone_verified?: boolean;
  two_factor_enabled?: boolean;
  login_count: number;
  last_login?: string | number | Date;
}

export interface ExchangeConfigDTO {
  id: string;
  name: string;
  api_key_masked?: string;
  status: 'active' | 'maintenance' | 'error' | 'inactive' | string;
  base_url?: string;
  created_at?: string | number | Date;
}

export interface HealthServiceDTO {
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  response_time: number;
}

export interface HealthDTO {
  status: string;
  services: Record<string, HealthServiceDTO>;
  error_rate: number;
}

export interface CandleDTO {
  timestamp: string | number | Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source?: string;
}

export interface MarketDataDTO {
  symbol: string;
  data: CandleDTO[];
  cached?: boolean;
  timestamp: string | number | Date;
}