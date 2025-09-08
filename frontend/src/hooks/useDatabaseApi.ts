/**
 * Hooks React pour l'utilisation des APIs de base de données
 */

import { useState, useEffect, useCallback } from 'react';
import { databaseApiService } from '../services/databaseApi';
import { Order, Position, User, AlertType } from '../types';

// Hook générique pour les données
export function useApiData<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  }, [apiCall, ...dependencies]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// Hook pour les ordres
export function useOrders(params?: {
  symbol?: string;
  status?: string;
  exchange?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}) {
  return useApiData(
    () => databaseApiService.getOrders(params),
    [JSON.stringify(params)]
  );
}

export function useOrder(id: string) {
  return useApiData(
    () => databaseApiService.getOrderById(id),
    [id]
  );
}

// Hook pour les positions
export function usePositions(params?: {
  symbol?: string;
  status?: string;
  exchange?: string;
  strategy_id?: string;
  limit?: number;
  offset?: number;
}) {
  return useApiData(
    () => databaseApiService.getPositions(params),
    [JSON.stringify(params)]
  );
}

export function usePosition(id: string) {
  return useApiData(
    () => databaseApiService.getPositionById(id),
    [id]
  );
}

// Hook pour les trades
export function useTrades(params?: {
  symbol?: string;
  exchange?: string;
  strategy_id?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}) {
  return useApiData(
    () => databaseApiService.getTrades(params),
    [JSON.stringify(params)]
  );
}

export function useTrade(id: string) {
  return useApiData(
    () => databaseApiService.getTradeById(id),
    [id]
  );
}

export function useTradesSummary(params?: {
  start_date?: string;
  end_date?: string;
  symbol?: string;
  exchange?: string;
}) {
  return useApiData(
    () => databaseApiService.getTradesSummary(params),
    [JSON.stringify(params)]
  );
}

// Hook pour le portefeuille
export function usePortfolioHistory(params?: {
  user_id?: string;
  trading_session_id?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}) {
  return useApiData(
    () => databaseApiService.getPortfolioHistory(params),
    [JSON.stringify(params)]
  );
}

export function usePortfolioSummary(params?: {
  user_id?: string;
  trading_session_id?: string;
}) {
  return useApiData(
    () => databaseApiService.getPortfolioSummary(params),
    [JSON.stringify(params)]
  );
}

// Hook pour les utilisateurs
export function useUsers(params?: {
  role?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useApiData(
    () => databaseApiService.getUsers(params),
    [JSON.stringify(params)]
  );
}

export function useUser(id: string) {
  return useApiData(
    () => databaseApiService.getUserById(id),
    [id]
  );
}

// Hook pour les exchanges
export function useExchanges(params?: {
  status?: string;
  exchange_type?: string;
  country?: string;
  feature?: string;
}) {
  return useApiData(
    () => databaseApiService.getExchanges(params),
    [JSON.stringify(params)]
  );
}

export function useExchange(id: string) {
  return useApiData(
    () => databaseApiService.getExchangeById(id),
    [id]
  );
}

// Hook pour les alertes
export function useAlerts(params?: {
  user_id?: string;
  alert_type?: string;
  severity?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useApiData(
    () => databaseApiService.getAlerts(params),
    [JSON.stringify(params)]
  );
}

export function useAlert(id: string) {
  return useApiData(
    () => databaseApiService.getAlertById(id),
    [id]
  );
}

// Hook pour les notifications
export function useNotifications(params?: {
  user_id?: string;
  channel?: string;
  is_sent?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useApiData(
    () => databaseApiService.getNotifications(params),
    [JSON.stringify(params)]
  );
}

export function useNotification(id: string) {
  return useApiData(
    () => databaseApiService.getNotificationById(id),
    [id]
  );
}

// Hook pour les métriques de performance
export function usePerformanceMetrics(params?: {
  metric_name?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}) {
  return useApiData(
    () => databaseApiService.getPerformanceMetrics(params),
    [JSON.stringify(params)]
  );
}

export function usePerformanceSummary() {
  return useApiData(() => databaseApiService.getPerformanceSummary());
}

// Hook pour les événements de sécurité
export function useSecurityEvents(params?: {
  user_id?: string;
  severity?: string;
  action?: string;
  limit?: number;
  offset?: number;
}) {
  return useApiData(
    () => databaseApiService.getSecurityEvents(params),
    [JSON.stringify(params)]
  );
}

export function useSecuritySummary() {
  return useApiData(() => databaseApiService.getSecuritySummary());
}

// Hook pour le statut de backup
export function useBackupStatus() {
  return useApiData(() => databaseApiService.getBackupStatus());
}

export function useBackupList(params?: {
  config_name?: string;
  limit?: number;
}) {
  return useApiData(
    () => databaseApiService.getBackupList(params),
    [JSON.stringify(params)]
  );
}

// Hook pour la santé du système
export function useSystemHealth() {
  return useApiData(() => databaseApiService.getHealth());
}

// Hook pour les mutations (création, mise à jour, suppression)
export function useMutation<T, P = any>(
  mutationFn: (params: P) => Promise<T>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<T | null>(null);

  const mutate = useCallback(async (params: P) => {
    try {
      setLoading(true);
      setError(null);
      const result = await mutationFn(params);
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Une erreur est survenue';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [mutationFn]);

  return { mutate, loading, error, data };
}

// Hooks spécifiques pour les mutations
export function useCreateOrder() {
  return useMutation(databaseApiService.createOrder);
}

export function useUpdateOrder() {
  return useMutation(({ id, data }: { id: string; data: Partial<Order> }) =>
    databaseApiService.updateOrder(id, data)
  );
}

export function useDeleteOrder() {
  return useMutation((id: string) => databaseApiService.deleteOrder(id));
}

export function useCreatePosition() {
  return useMutation(databaseApiService.createPosition);
}

export function useUpdatePosition() {
  return useMutation(({ id, data }: { id: string; data: Partial<Position> }) =>
    databaseApiService.updatePosition(id, data)
  );
}

export function useClosePosition() {
  return useMutation((id: string) => databaseApiService.closePosition(id));
}

export function useCreateUser() {
  return useMutation(databaseApiService.createUser);
}

export function useUpdateUser() {
  return useMutation(({ id, data }: { id: string; data: Partial<User> }) =>
    databaseApiService.updateUser(id, data)
  );
}

export function useDeleteUser() {
  return useMutation((id: string) => databaseApiService.deleteUser(id));
}

export function useCreateAlert() {
  return useMutation(databaseApiService.createAlert);
}

export function useUpdateAlert() {
  return useMutation(({ id, data }: { id: string; data: Partial<AlertType> }) =>
    databaseApiService.updateAlert(id, data)
  );
}

export function useDeleteAlert() {
  return useMutation((id: string) => databaseApiService.deleteAlert(id));
}

export function useExecuteBackup() {
  return useMutation((configName: string) => databaseApiService.executeBackup(configName));
}