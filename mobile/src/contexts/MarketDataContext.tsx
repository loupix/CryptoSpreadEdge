// Contexte pour les données de marché
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { MarketData, ArbitrageOpportunity, IndicatorData } from '../types';
import { apiService } from '../services/api';
import { wsService } from '../services/websocket';

interface MarketDataContextType {
  marketData: MarketData[];
  arbitrageOpportunities: ArbitrageOpportunity[];
  indicators: IndicatorData[];
  isLoading: boolean;
  error: string | null;
  subscribeToSymbols: (symbols: string[]) => void;
  unsubscribeFromSymbols: () => void;
  refreshData: () => Promise<void>;
  getMarketDataForSymbol: (symbol: string) => MarketData | undefined;
  getArbitrageForSymbol: (symbol: string) => ArbitrageOpportunity[];
}

const MarketDataContext = createContext<MarketDataContextType | undefined>(undefined);

interface MarketDataProviderProps {
  children: ReactNode;
}

export const MarketDataProvider: React.FC<MarketDataProviderProps> = ({ children }) => {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [arbitrageOpportunities, setArbitrageOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [indicators, setIndicators] = useState<IndicatorData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subscribedSymbols, setSubscribedSymbols] = useState<string[]>([]);

  useEffect(() => {
    // Configurer les listeners WebSocket
    wsService.on('market_data', handleMarketDataUpdate);
    wsService.on('arbitrage_opportunity', handleArbitrageUpdate);
    wsService.on('connected', handleWebSocketConnected);
    wsService.on('disconnected', handleWebSocketDisconnected);

    // Charger les données initiales
    loadInitialData();

    return () => {
      wsService.off('market_data', handleMarketDataUpdate);
      wsService.off('arbitrage_opportunity', handleArbitrageUpdate);
      wsService.off('connected', handleWebSocketConnected);
      wsService.off('disconnected', handleWebSocketDisconnected);
    };
  }, []);

  const handleMarketDataUpdate = (data: MarketData) => {
    setMarketData(prev => {
      const existingIndex = prev.findIndex(item => 
        item.symbol === data.symbol && item.platform === data.platform
      );
      
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = data;
        return updated;
      } else {
        return [...prev, data];
      }
    });
  };

  const handleArbitrageUpdate = (data: ArbitrageOpportunity) => {
    setArbitrageOpportunities(prev => {
      const existingIndex = prev.findIndex(item => item.id === data.id);
      
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = data;
        return updated;
      } else {
        return [...prev, data];
      }
    });
  };

  const handleWebSocketConnected = () => {
    console.log('WebSocket connecté, re-souscription aux symboles');
    if (subscribedSymbols.length > 0) {
      wsService.subscribeToMarketData(subscribedSymbols);
      wsService.subscribeToArbitrage();
    }
  };

  const handleWebSocketDisconnected = () => {
    console.log('WebSocket déconnecté');
  };

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Charger les données de marché pour les symboles principaux
      const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'];
      const marketResponse = await apiService.getMarketData({ symbols });
      
      if (marketResponse.success && marketResponse.data) {
        setMarketData(marketResponse.data);
      }

      // Charger les opportunités d'arbitrage
      const arbitrageResponse = await apiService.getArbitrageOpportunities();
      
      if (arbitrageResponse.success && arbitrageResponse.data) {
        setArbitrageOpportunities(arbitrageResponse.data);
      }

    } catch (err) {
      setError('Erreur lors du chargement des données');
      console.error('Erreur loadInitialData:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const subscribeToSymbols = (symbols: string[]) => {
    setSubscribedSymbols(symbols);
    wsService.subscribeToMarketData(symbols);
    wsService.subscribeToArbitrage();
  };

  const unsubscribeFromSymbols = () => {
    setSubscribedSymbols([]);
    wsService.unsubscribe('market_data');
    wsService.unsubscribe('arbitrage');
  };

  const refreshData = async () => {
    await loadInitialData();
  };

  const getMarketDataForSymbol = (symbol: string): MarketData | undefined => {
    return marketData.find(data => data.symbol === symbol);
  };

  const getArbitrageForSymbol = (symbol: string): ArbitrageOpportunity[] => {
    return arbitrageOpportunities.filter(opp => opp.symbol === symbol);
  };

  const value: MarketDataContextType = {
    marketData,
    arbitrageOpportunities,
    indicators,
    isLoading,
    error,
    subscribeToSymbols,
    unsubscribeFromSymbols,
    refreshData,
    getMarketDataForSymbol,
    getArbitrageForSymbol,
  };

  return (
    <MarketDataContext.Provider value={value}>
      {children}
    </MarketDataContext.Provider>
  );
};

export const useMarketData = (): MarketDataContextType => {
  const context = useContext(MarketDataContext);
  if (context === undefined) {
    throw new Error('useMarketData must be used within a MarketDataProvider');
  }
  return context;
};