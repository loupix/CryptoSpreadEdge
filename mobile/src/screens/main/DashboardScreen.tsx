// Écran du tableau de bord principal
import React, { useEffect, useState } from 'react';
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
import { useMarketData } from '../../contexts/MarketDataContext';
import { useAuth } from '../../contexts/AuthContext';
import { MarketData, ArbitrageOpportunity } from '../../types';

const { width } = Dimensions.get('window');

const DashboardScreen = ({ navigation }: any) => {
  const { theme } = useTheme();
  const { user } = useAuth();
  const { 
    marketData, 
    arbitrageOpportunities, 
    isLoading, 
    refreshData,
    getArbitrageForSymbol 
  } = useMarketData();

  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    // Souscrire aux données des symboles principaux
    const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'];
    // Note: La souscription sera gérée par le contexte
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshData();
    setRefreshing(false);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 8,
    }).format(price);
  };

  const formatChange = (change: number, percent: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${percent.toFixed(2)}%)`;
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? theme.colors.success : theme.colors.error;
  };

  const renderMarketCard = (data: MarketData) => (
    <TouchableOpacity key={`${data.symbol}-${data.platform}`} style={styles.marketCard}>
      <View style={styles.marketHeader}>
        <Text style={[styles.symbol, { color: theme.colors.text }]}>
          {data.symbol}
        </Text>
        <Text style={[styles.platform, { color: theme.colors.textSecondary }]}>
          {data.platform}
        </Text>
      </View>
      <Text style={[styles.price, { color: theme.colors.text }]}>
        {formatPrice(data.price)}
      </Text>
      <Text style={[styles.change, { color: getChangeColor(data.change24h) }]}>
        {formatChange(data.change24h, data.changePercent24h)}
      </Text>
    </TouchableOpacity>
  );

  const renderArbitrageCard = (opportunity: ArbitrageOpportunity) => (
    <TouchableOpacity key={opportunity.id} style={styles.arbitrageCard}>
      <View style={styles.arbitrageHeader}>
        <Text style={[styles.arbitrageSymbol, { color: theme.colors.text }]}>
          {opportunity.symbol}
        </Text>
        <View style={[styles.profitBadge, { backgroundColor: theme.colors.success }]}>
          <Text style={styles.profitText}>
            +{opportunity.profit.toFixed(2)}$
          </Text>
        </View>
      </View>
      <View style={styles.arbitrageDetails}>
        <View style={styles.platformInfo}>
          <Text style={[styles.platformLabel, { color: theme.colors.textSecondary }]}>
            Achat: {opportunity.buyPlatform}
          </Text>
          <Text style={[styles.platformPrice, { color: theme.colors.text }]}>
            {formatPrice(opportunity.buyPrice)}
          </Text>
        </View>
        <View style={styles.platformInfo}>
          <Text style={[styles.platformLabel, { color: theme.colors.textSecondary }]}>
            Vente: {opportunity.sellPlatform}
          </Text>
          <Text style={[styles.platformPrice, { color: theme.colors.text }]}>
            {formatPrice(opportunity.sellPrice)}
          </Text>
        </View>
      </View>
      <Text style={[styles.spread, { color: theme.colors.primary }]}>
        Spread: {opportunity.spreadPercent.toFixed(2)}%
      </Text>
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
    welcomeText: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.xs,
    },
    subtitle: {
      fontSize: 16,
      color: theme.colors.textSecondary,
    },
    content: {
      flex: 1,
      padding: theme.spacing.lg,
    },
    section: {
      marginBottom: theme.spacing.xl,
    },
    sectionTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    marketGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
    },
    marketCard: {
      width: (width - theme.spacing.lg * 3) / 2,
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.md,
      marginBottom: theme.spacing.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    marketHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing.sm,
    },
    symbol: {
      fontSize: 16,
      fontWeight: 'bold',
    },
    platform: {
      fontSize: 12,
    },
    price: {
      fontSize: 18,
      fontWeight: 'bold',
      marginBottom: theme.spacing.xs,
    },
    change: {
      fontSize: 14,
      fontWeight: '600',
    },
    arbitrageCard: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.md,
      marginBottom: theme.spacing.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    arbitrageHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing.md,
    },
    arbitrageSymbol: {
      fontSize: 18,
      fontWeight: 'bold',
    },
    profitBadge: {
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: theme.spacing.xs,
      borderRadius: 8,
    },
    profitText: {
      color: 'white',
      fontSize: 14,
      fontWeight: 'bold',
    },
    arbitrageDetails: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: theme.spacing.sm,
    },
    platformInfo: {
      flex: 1,
    },
    platformLabel: {
      fontSize: 12,
      marginBottom: theme.spacing.xs,
    },
    platformPrice: {
      fontSize: 16,
      fontWeight: '600',
    },
    spread: {
      fontSize: 14,
      fontWeight: '600',
      textAlign: 'center',
    },
    quickActions: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginTop: theme.spacing.lg,
    },
    actionButton: {
      alignItems: 'center',
      padding: theme.spacing.md,
    },
    actionIcon: {
      marginBottom: theme.spacing.sm,
    },
    actionText: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.welcomeText}>
          Bonjour, {user?.username || 'Utilisateur'} !
        </Text>
        <Text style={styles.subtitle}>
          Tableau de bord CryptoSpreadEdge
        </Text>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Marchés en temps réel</Text>
          <View style={styles.marketGrid}>
            {marketData.map(renderMarketCard)}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Opportunités d'arbitrage</Text>
          {arbitrageOpportunities.length > 0 ? (
            arbitrageOpportunities.slice(0, 5).map(renderArbitrageCard)
          ) : (
            <View style={styles.arbitrageCard}>
              <Text style={[styles.spread, { color: theme.colors.textSecondary }]}>
                Aucune opportunité d'arbitrage disponible
              </Text>
            </View>
          )}
        </View>

        <View style={styles.quickActions}>
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => navigation.navigate('Trading')}
          >
            <Icon name="trending-up" size={32} color={theme.colors.primary} />
            <Text style={styles.actionText}>Trading</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => navigation.navigate('Portfolio')}
          >
            <Icon name="account-balance-wallet" size={32} color={theme.colors.primary} />
            <Text style={styles.actionText}>Portefeuille</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => navigation.navigate('Arbitrage')}
          >
            <Icon name="swap-horiz" size={32} color={theme.colors.primary} />
            <Text style={styles.actionText}>Arbitrage</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

export default DashboardScreen;