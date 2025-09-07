// Écran des opportunités d'arbitrage
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { useTheme } from '../../contexts/ThemeContext';
import { useMarketData } from '../../contexts/MarketDataContext';
import { apiService } from '../../services/api';
import { ArbitrageOpportunity } from '../../types';

const ArbitrageScreen = ({ navigation }: any) => {
  const { theme } = useTheme();
  const { arbitrageOpportunities, isLoading, refreshData } = useMarketData();
  const [refreshing, setRefreshing] = useState(false);
  const [sortBy, setSortBy] = useState<'profit' | 'spread' | 'confidence'>('profit');

  useEffect(() => {
    // Les opportunités sont déjà chargées par le contexte
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshData();
    setRefreshing(false);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 8,
    }).format(amount);
  };

  const formatPercentage = (percent: number) => {
    return `${percent.toFixed(2)}%`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return theme.colors.success;
    if (confidence >= 0.6) return theme.colors.warning;
    return theme.colors.error;
  };

  const getConfidenceText = (confidence: number) => {
    if (confidence >= 0.8) return 'Élevée';
    if (confidence >= 0.6) return 'Moyenne';
    return 'Faible';
  };

  const sortOpportunities = (opportunities: ArbitrageOpportunity[]) => {
    return [...opportunities].sort((a, b) => {
      switch (sortBy) {
        case 'profit':
          return b.profit - a.profit;
        case 'spread':
          return b.spreadPercent - a.spreadPercent;
        case 'confidence':
          return b.confidence - a.confidence;
        default:
          return 0;
      }
    });
  };

  const handleExecuteArbitrage = async (opportunity: ArbitrageOpportunity) => {
    Alert.alert(
      'Exécuter l\'arbitrage',
      `Voulez-vous exécuter cet arbitrage pour ${opportunity.symbol} ?\nProfit estimé: ${formatCurrency(opportunity.profit)}`,
      [
        { text: 'Annuler', style: 'cancel' },
        { 
          text: 'Exécuter', 
          onPress: async () => {
            try {
              // Ici on pourrait appeler une API pour exécuter l'arbitrage
              Alert.alert('Succès', 'Arbitrage exécuté avec succès');
            } catch (error) {
              Alert.alert('Erreur', 'Erreur lors de l\'exécution de l\'arbitrage');
            }
          }
        }
      ]
    );
  };

  const renderSortButtons = () => (
    <View style={styles.sortContainer}>
      <Text style={[styles.sortLabel, { color: theme.colors.text }]}>
        Trier par:
      </Text>
      <View style={styles.sortButtons}>
        {[
          { key: 'profit', label: 'Profit' },
          { key: 'spread', label: 'Spread' },
          { key: 'confidence', label: 'Confiance' },
        ].map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            style={[
              styles.sortButton,
              sortBy === key && styles.selectedSortButton
            ]}
            onPress={() => setSortBy(key as any)}
          >
            <Text style={[
              styles.sortButtonText,
              sortBy === key && styles.selectedSortButtonText
            ]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderOpportunity = (opportunity: ArbitrageOpportunity) => (
    <TouchableOpacity 
      key={opportunity.id} 
      style={styles.opportunityCard}
      onPress={() => handleExecuteArbitrage(opportunity)}
    >
      <View style={styles.opportunityHeader}>
        <View style={styles.symbolContainer}>
          <Text style={[styles.symbol, { color: theme.colors.text }]}>
            {opportunity.symbol}
          </Text>
          <View style={[
            styles.confidenceBadge,
            { backgroundColor: getConfidenceColor(opportunity.confidence) }
          ]}>
            <Text style={styles.confidenceText}>
              {getConfidenceText(opportunity.confidence)}
            </Text>
          </View>
        </View>
        <View style={styles.profitContainer}>
          <Text style={[styles.profit, { color: theme.colors.success }]}>
            +{formatCurrency(opportunity.profit)}
          </Text>
          <Text style={[styles.profitLabel, { color: theme.colors.textSecondary }]}>
            Profit estimé
          </Text>
        </View>
      </View>

      <View style={styles.platformsContainer}>
        <View style={styles.platformInfo}>
          <View style={styles.platformHeader}>
            <Icon name="trending-up" size={16} color={theme.colors.success} />
            <Text style={[styles.platformName, { color: theme.colors.text }]}>
              Achat: {opportunity.buyPlatform}
            </Text>
          </View>
          <Text style={[styles.platformPrice, { color: theme.colors.text }]}>
            {formatCurrency(opportunity.buyPrice)}
          </Text>
        </View>

        <View style={styles.arrowContainer}>
          <Icon name="arrow-forward" size={24} color={theme.colors.primary} />
        </View>

        <View style={styles.platformInfo}>
          <View style={styles.platformHeader}>
            <Icon name="trending-down" size={16} color={theme.colors.error} />
            <Text style={[styles.platformName, { color: theme.colors.text }]}>
              Vente: {opportunity.sellPlatform}
            </Text>
          </View>
          <Text style={[styles.platformPrice, { color: theme.colors.text }]}>
            {formatCurrency(opportunity.sellPrice)}
          </Text>
        </View>
      </View>

      <View style={styles.metricsContainer}>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
            Spread
          </Text>
          <Text style={[styles.metricValue, { color: theme.colors.primary }]}>
            {formatPercentage(opportunity.spreadPercent)}
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
            Confiance
          </Text>
          <Text style={[
            styles.metricValue,
            { color: getConfidenceColor(opportunity.confidence) }
          ]}>
            {formatPercentage(opportunity.confidence * 100)}
          </Text>
        </View>
        <View style={styles.metric}>
          <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
            Délai
          </Text>
          <Text style={[styles.metricValue, { color: theme.colors.text }]}>
            {new Date(opportunity.timestamp).toLocaleTimeString('fr-FR')}
          </Text>
        </View>
      </View>

      <View style={styles.actionContainer}>
        <TouchableOpacity
          style={[styles.executeButton, { backgroundColor: theme.colors.primary }]}
          onPress={() => handleExecuteArbitrage(opportunity)}
        >
          <Icon name="play-arrow" size={20} color="white" />
          <Text style={styles.executeButtonText}>Exécuter</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
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
      marginBottom: theme.spacing.md,
    },
    content: {
      flex: 1,
      padding: theme.spacing.lg,
    },
    sortContainer: {
      marginBottom: theme.spacing.lg,
    },
    sortLabel: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: theme.spacing.sm,
    },
    sortButtons: {
      flexDirection: 'row',
      gap: theme.spacing.sm,
    },
    sortButton: {
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      borderRadius: 20,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface,
    },
    selectedSortButton: {
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    sortButtonText: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.colors.text,
    },
    selectedSortButtonText: {
      color: 'white',
    },
    opportunityCard: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.md,
      marginBottom: theme.spacing.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    opportunityHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: theme.spacing.md,
    },
    symbolContainer: {
      flex: 1,
    },
    symbol: {
      fontSize: 20,
      fontWeight: 'bold',
      marginBottom: theme.spacing.xs,
    },
    confidenceBadge: {
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: theme.spacing.xs,
      borderRadius: 12,
      alignSelf: 'flex-start',
    },
    confidenceText: {
      color: 'white',
      fontSize: 12,
      fontWeight: 'bold',
    },
    profitContainer: {
      alignItems: 'flex-end',
    },
    profit: {
      fontSize: 18,
      fontWeight: 'bold',
      marginBottom: theme.spacing.xs,
    },
    profitLabel: {
      fontSize: 12,
    },
    platformsContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: theme.spacing.md,
    },
    platformInfo: {
      flex: 1,
    },
    platformHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: theme.spacing.xs,
    },
    platformName: {
      fontSize: 14,
      fontWeight: '600',
      marginLeft: theme.spacing.xs,
    },
    platformPrice: {
      fontSize: 16,
      fontWeight: 'bold',
    },
    arrowContainer: {
      paddingHorizontal: theme.spacing.sm,
    },
    metricsContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: theme.spacing.md,
      paddingTop: theme.spacing.md,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    metric: {
      alignItems: 'center',
      flex: 1,
    },
    metricLabel: {
      fontSize: 12,
      marginBottom: theme.spacing.xs,
    },
    metricValue: {
      fontSize: 14,
      fontWeight: 'bold',
    },
    actionContainer: {
      alignItems: 'center',
    },
    executeButton: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: theme.spacing.lg,
      paddingVertical: theme.spacing.md,
      borderRadius: 25,
    },
    executeButtonText: {
      color: 'white',
      fontSize: 16,
      fontWeight: 'bold',
      marginLeft: theme.spacing.sm,
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
    },
  });

  const sortedOpportunities = sortOpportunities(arbitrageOpportunities);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Arbitrage</Text>
        <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
          Opportunités de profit entre plateformes
        </Text>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {renderSortButtons()}

        {sortedOpportunities.length > 0 ? (
          sortedOpportunities.map(renderOpportunity)
        ) : (
          <View style={styles.emptyState}>
            <Icon 
              name="swap-horiz" 
              size={64} 
              color={theme.colors.textSecondary}
              style={styles.emptyIcon}
            />
            <Text style={styles.emptyTitle}>Aucune opportunité</Text>
            <Text style={styles.emptyText}>
              Aucune opportunité d'arbitrage disponible pour le moment
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

export default ArbitrageScreen;