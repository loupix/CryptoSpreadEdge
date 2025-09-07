// Service WebSocket pour les données temps réel
import { WebSocketMessage, MarketData, Order, Portfolio, ArbitrageOpportunity } from '../types';

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;
  private isConnected = false;
  private listeners: Map<string, ((data: any) => void)[]> = new Map();

  private wsUrl = __DEV__ 
    ? 'ws://localhost:8000/ws' 
    : 'wss://api.cryptospreadedge.com/ws';

  constructor() {
    this.connect();
  }

  private connect() {
    try {
      this.ws = new WebSocket(this.wsUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket connecté');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.emit('connected', {});
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Erreur parsing message WebSocket:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket fermé');
        this.isConnected = false;
        this.emit('disconnected', {});
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('Erreur WebSocket:', error);
        this.emit('error', error);
      };

    } catch (error) {
      console.error('Erreur connexion WebSocket:', error);
      this.handleReconnect();
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Impossible de se reconnecter au WebSocket');
      this.emit('reconnect_failed', {});
    }
  }

  private handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'market_data':
        this.emit('market_data', message.data);
        break;
      case 'order_update':
        this.emit('order_update', message.data);
        break;
      case 'portfolio_update':
        this.emit('portfolio_update', message.data);
        break;
      case 'arbitrage_opportunity':
        this.emit('arbitrage_opportunity', message.data);
        break;
      default:
        console.log('Type de message non géré:', message.type);
    }
  }

  private emit(event: string, data: any) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error('Erreur dans le listener:', error);
        }
      });
    }
  }

  // Méthodes publiques
  public on(event: string, listener: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(listener);
  }

  public off(event: string, listener: (data: any) => void) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      const index = eventListeners.indexOf(listener);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }

  public subscribeToMarketData(symbols: string[]) {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'market_data',
        symbols: symbols
      }));
    }
  }

  public subscribeToOrders() {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'orders'
      }));
    }
  }

  public subscribeToPortfolio() {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'portfolio'
      }));
    }
  }

  public subscribeToArbitrage() {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channel: 'arbitrage'
      }));
    }
  }

  public unsubscribe(channel: string) {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        channel: channel
      }));
    }
  }

  public send(message: any) {
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket non connecté, impossible d\'envoyer le message');
    }
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.listeners.clear();
  }

  public getConnectionStatus(): boolean {
    return this.isConnected;
  }

  public reconnect() {
    this.reconnectAttempts = 0;
    this.connect();
  }
}

export const wsService = new WebSocketService();
export default wsService;