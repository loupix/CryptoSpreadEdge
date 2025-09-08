// Types pour les messages/streams Redis (via WS/API)

export interface RedisStreamMessage<T = unknown> {
  id: string;
  stream: string;
  payload: T;
  timestamp: number;
}

export interface MarketTickPayload {
  symbol: string;
  price: number;
  volume: number;
}

export interface AlertEventPayload {
  id: string;
  name: string;
  severity: string;
  symbol?: string;
  message?: string;
}