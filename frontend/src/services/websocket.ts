import { io, Socket } from 'socket.io-client';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

class WebSocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Array<(data: any) => void>> = new Map();

  connect(): void {
    if (this.socket?.connected) {
      return;
    }

    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    this.socket = io(wsUrl, {
      transports: ['websocket'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connecté');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket déconnecté');
    });

    this.socket.on('error', (error) => {
      console.error('Erreur WebSocket:', error);
    });

    // Écouter les messages génériques
    this.socket.on('message', (message: WebSocketMessage) => {
      this.handleMessage(message);
    });

    // Écouter les mises à jour spécifiques
    this.socket.on('market-data-update', (data) => {
      this.notifyListeners('market-data', data);
    });

    this.socket.on('indicators-update', (data) => {
      this.notifyListeners('indicators', data);
    });

    this.socket.on('predictions-update', (data) => {
      this.notifyListeners('predictions', data);
    });

    this.socket.on('arbitrage-update', (data) => {
      this.notifyListeners('arbitrage', data);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribe(event: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    
    this.listeners.get(event)!.push(callback);

    // Retourner une fonction de désabonnement
    return () => {
      const listeners = this.listeners.get(event);
      if (listeners) {
        const index = listeners.indexOf(callback);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    this.notifyListeners(message.type, message.data);
  }

  private notifyListeners(event: string, data: any): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Erreur dans le listener pour ${event}:`, error);
        }
      });
    }
  }

  // Méthodes pour émettre des événements
  emit(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  // Méthodes spécifiques pour les services
  subscribeToMarketData(callback: (data: any) => void): () => void {
    return this.subscribe('market-data', callback);
  }

  subscribeToIndicators(callback: (data: any) => void): () => void {
    return this.subscribe('indicators', callback);
  }

  subscribeToPredictions(callback: (data: any) => void): () => void {
    return this.subscribe('predictions', callback);
  }

  subscribeToArbitrage(callback: (data: any) => void): () => void {
    return this.subscribe('arbitrage', callback);
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsService = new WebSocketService();
export default wsService;