// Écran du portefeuille
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';

import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';
import { Portfolio, Position } from '../../types';

const { width } = Dimensions.get('window');

const PortfolioScreen = ({ navigation }: any) => {
  const { theme } = useTheme();
  const { user } = useAuth();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = async () => {
    try {
      setIsLoading(true);
      const [portfolioResponse, positionsResponse] = await Promise.all([
        apiService.getPortfolio(),
        apiService.getPositions()
      ]);

      if (portfolioResponse.success && portfolioResponse.data) {
        setPortfolio(portfolioResponse.data);
      }

      if (positionsResponse.success && positionsResponse.data) {
        setPositions(positionsResponse.data);
      }
    } catch (error) {
      console.error('Erreur chargement portefeuille:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPortfolioData();
    setRefreshing(false);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercentage = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(2)}%`;
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? theme.colors.success : theme.colors.error;
  };

  const renderPortfolioSummary = () => {
    if (!portfolio) return null;

    return (
      <LinearGradient
        colors={[theme.colors.primary, theme.colors.secondary]}
        style={styles.summaryCard}
      >
        <Text style={styles.summaryTitle}>Valeur totale</Text>
        <Text style={styles.totalValue}>
          {formatCurrency(portfolio.totalValue)}
        </Text>
        <View style={styles.changeContainer}>
          <Text style={[
            styles.changeText,
            { color: getChangeColor(portfolio.totalValueChange) }
          ]}>
            {formatCurrency(portfolio.totalValueChange)} ({formatPercentage(portfolio.totalValueChangePercent)})
          </Text>
          <Text style={styles.changeLabel}>24h</Text>
        </View>
        <View style={styles.cashContainer}>
          <Text style={styles.cashLabel}>Liquidités</Text>
          <Text style={styles.cashValue}>
            {formatCurrency(portfolio.cash)}
          </Text>
        </View>
      </LinearGradient>
    );
  };

  const renderPosition = (position: Position) => (
    <TouchableOpacity key={position.symbol} style={styles.positionCard}>
      <View style={styles.positionHeader}>
        <View style={styles.positionInfo}>
          <Text style={[styles.positionSymbol, { color: theme.colors.text }]}>
            {position.symbol}
          </Text>
          <Text style={[styles.positionPlatform, { color: theme.colors.textSecondary }]}>
            {position.platform}
          </Text>
        </View>
        <View style={styles.positionValue}>
          <Text style={[styles.positionValueText, { color: theme.colors.text }]}>
            {formatCurrency(position.value)}
          </Text>
          <Text style={[
            styles.positionPnl,
            { color: getChangeColor(position.pnl) }
          ]}>
            {formatCurrency(position.pnl)} ({formatPercentage(position.pnlPercent)})
          </Text>
        </View>
      </View>
      <View style={styles.positionDetails}>
        <View style={styles.positionDetail}>
          <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
            Quantité
          </Text>
          <Text style={[styles.detailValue, { color: theme.colors.text }]}>
            {position.quantity.toFixed(8)}
          </Text>
        </View>
        <View style={styles.positionDetail}>
          <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
            Prix moyen
          </Text>
          <Text style={[styles.detailValue, { color: theme.colors.text }]}>
            {formatCurrency(position.averagePrice)}
          </Text>
        </View>
        <View style={styles.positionDetail}>
          <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
            Prix actuel
          </Text>
          <Text style={[styles.detailValue, { color: theme.colors.text }]}>
            {formatCurrency(position.currentPrice)}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderQuickActions = () => (
    <View style={styles.quickActions}>
      <TouchableOpacity 
        style={styles.actionButton}
        onPress={() => navigation.navigate('Trading')}
      >
        <Icon name="add" size={24} color={theme.colors.primary} />
        <Text style={[styles.actionText, { color: theme.colors.primary }]}>
          Acheter
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={styles.actionButton}
        onPress={() => navigation.navigate('Trading')}
      >
        <Icon name="remove" size={24} color={theme.colors.error} />
        <Text style={[styles.actionText, { color: theme.colors.error }]}>
          Vendre
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={styles.actionButton}
        onPress={() => navigation.navigate('Arbitrage')}
      >
        <Icon name="swap-horiz" size={24} color={theme.colors.warning} />
        <Text style={[styles.actionText, { color: theme.colors.warning }]}>
          Arbitrage
        </Text>
      </TouchableOpacity>
    </View>
  );

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    header: {
      padding: theme.spacing.lg,
      backgroundColor: theme.colors.surface,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.colors.text,
    },
    content: {
      flex: 1,
      padding: theme.spacing.lg,
    },
    summaryCard: {
      borderRadius: 16,
      padding: theme.spacing.lg,
      marginBottom: theme.spacing.lg,
      alignItems: 'center',
    },
    summaryTitle: {
      fontSize: 16,
      color: 'rgba(255,255,255,0.8)',
      marginBottom: theme.spacing.sm,
    },
    totalValue: {
      fontSize: 36,
      fontWeight: 'bold',
      color: 'white',
      marginBottom: theme.spacing.sm,
    },
    changeContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: theme.spacing.lg,
    },
    changeText: {
      fontSize: 16,
      fontWeight: '600',
      marginRight: theme.spacing.sm,
    },
    changeLabel: {
      fontSize: 14,
      color: 'rgba(255,255,255,0.8)',
    },
    cashContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      width: '100%',
      paddingTop: theme.spacing.md,
      borderTopWidth: 1,
      borderTopColor: 'rgba(255,255,255,0.2)',
    },
    cashLabel: {
      fontSize: 14,
      color: 'rgba(255,255,255,0.8)',
    },
    cashValue: {
      fontSize: 16,
      fontWeight: '600',
      color: 'white',
    },
    positionsSection: {
      marginBottom: theme.spacing.lg,
    },
    sectionTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    positionCard: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.md,
      marginBottom: theme.spacing.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    positionHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: theme.spacing.md,
    },
    positionInfo: {
      flex: 1,
    },
    positionSymbol: {
      fontSize: 18,
      fontWeight: 'bold',
      marginBottom: theme.spacing.xs,
    },
    positionPlatform: {
      fontSize: 14,
    },
    positionValue: {
      alignItems: 'flex-end',
    },
    positionValueText: {
      fontSize: 16,
      fontWeight: 'bold',
      marginBottom: theme.spacing.xs,
    },
    positionPnl: {
      fontSize: 14,
      fontWeight: '600',
    },
    positionDetails: {
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
    positionDetail: {
      flex: 1,
      alignItems: 'center',
    },
    detailLabel: {
      fontSize: 12,
      marginBottom: theme.spacing.xs,
    },
    detailValue: {
      fontSize: 14,
      fontWeight: '600',
    },
    quickActions: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      paddingVertical: theme.spacing.lg,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    actionButton: {
      alignItems: 'center',
      padding: theme.spacing.md,
    },
    actionText: {
      fontSize: 14,
      fontWeight: '600',
      marginTop: theme.spacing.sm,
    },
    emptyState: {
      alignItems: 'center',
      paddingVertical: theme.spacing.xl * 2,
    },
    emptyIcon: {
      marginBottom: theme.spacing.lg,
    },
    emptyTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.sm,
    },
    emptyText: {
      fontSize: 16,
      color: theme.colors.textSecondary,
      textAlign: 'center',
      marginBottom: theme.spacing.lg,
    },
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Portefeuille</Text>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {renderPortfolioSummary()}

        <View style={styles.positionsSection}>
          <Text style={styles.sectionTitle}>Positions</Text>
          {positions.length > 0 ? (
            positions.map(renderPosition)
          ) : (
            <View style={styles.emptyState}>
              <Icon 
                name="account-balance-wallet" 
                size={64} 
                color={theme.colors.textSecondary}
                style={styles.emptyIcon}
              />
              <Text style={styles.emptyTitle}>Aucune position</Text>
              <Text style={styles.emptyText}>
                Commencez à trader pour voir vos positions ici
              </Text>
            </View>
          )}
        </View>

        {renderQuickActions()}
      </ScrollView>
    </View>
  );
};

export default PortfolioScreen;