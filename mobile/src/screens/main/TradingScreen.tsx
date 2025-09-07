// Écran de trading
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { useTheme } from '../../contexts/ThemeContext';
import { useMarketData } from '../../contexts/MarketDataContext';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';
import { TradingRequest, Order } from '../../types';

const TradingScreen = ({ navigation }: any) => {
  const { theme } = useTheme();
  const { user } = useAuth();
  const { marketData, getMarketDataForSymbol } = useMarketData();

  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [orderSide, setOrderSide] = useState<'market' | 'limit'>('market');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [isOrderModalVisible, setIsOrderModalVisible] = useState(false);
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'];

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await apiService.getOrders();
      if (response.success && response.data) {
        setOrders(response.data);
      }
    } catch (error) {
      console.error('Erreur chargement ordres:', error);
    }
  };

  const getCurrentPrice = () => {
    const data = getMarketDataForSymbol(selectedSymbol);
    return data?.price || 0;
  };

  const handlePlaceOrder = async () => {
    if (!quantity || parseFloat(quantity) <= 0) {
      Alert.alert('Erreur', 'Veuillez entrer une quantité valide');
      return;
    }

    if (orderSide === 'limit' && (!price || parseFloat(price) <= 0)) {
      Alert.alert('Erreur', 'Veuillez entrer un prix valide pour un ordre limite');
      return;
    }

    setIsLoading(true);
    try {
      const orderRequest: TradingRequest = {
        symbol: selectedSymbol,
        side: orderType,
        type: orderSide,
        quantity: parseFloat(quantity),
        price: orderSide === 'limit' ? parseFloat(price) : undefined,
        platform: 'binance', // Par défaut
      };

      const response = await apiService.placeOrder(orderRequest);
      
      if (response.success) {
        Alert.alert('Succès', 'Ordre placé avec succès');
        setIsOrderModalVisible(false);
        setQuantity('');
        setPrice('');
        loadOrders();
      } else {
        Alert.alert('Erreur', response.error || 'Erreur lors du placement de l\'ordre');
      }
    } catch (error) {
      Alert.alert('Erreur', 'Erreur lors du placement de l\'ordre');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      const response = await apiService.cancelOrder(orderId);
      if (response.success) {
        Alert.alert('Succès', 'Ordre annulé');
        loadOrders();
      } else {
        Alert.alert('Erreur', 'Erreur lors de l\'annulation de l\'ordre');
      }
    } catch (error) {
      Alert.alert('Erreur', 'Erreur lors de l\'annulation de l\'ordre');
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 8,
    }).format(price);
  };

  const getOrderStatusColor = (status: string) => {
    switch (status) {
      case 'filled': return theme.colors.success;
      case 'pending': return theme.colors.warning;
      case 'cancelled': return theme.colors.error;
      default: return theme.colors.textSecondary;
    }
  };

  const getOrderStatusText = (status: string) => {
    switch (status) {
      case 'filled': return 'Exécuté';
      case 'pending': return 'En attente';
      case 'cancelled': return 'Annulé';
      case 'rejected': return 'Rejeté';
      default: return status;
    }
  };

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
    symbolSelector: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: theme.spacing.sm,
    },
    symbolButton: {
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      borderRadius: 20,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    selectedSymbolButton: {
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    symbolButtonText: {
      color: theme.colors.text,
      fontWeight: '600',
    },
    selectedSymbolButtonText: {
      color: 'white',
    },
    content: {
      flex: 1,
      padding: theme.spacing.lg,
    },
    priceCard: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.lg,
      marginBottom: theme.spacing.lg,
      alignItems: 'center',
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    currentPrice: {
      fontSize: 32,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.sm,
    },
    priceChange: {
      fontSize: 16,
      color: theme.colors.success,
    },
    orderButton: {
      backgroundColor: theme.colors.primary,
      borderRadius: 12,
      paddingVertical: theme.spacing.md,
      alignItems: 'center',
      marginBottom: theme.spacing.lg,
    },
    orderButtonText: {
      color: 'white',
      fontSize: 18,
      fontWeight: 'bold',
    },
    ordersSection: {
      marginTop: theme.spacing.lg,
    },
    sectionTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    orderCard: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.md,
      marginBottom: theme.spacing.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    orderHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing.sm,
    },
    orderSymbol: {
      fontSize: 16,
      fontWeight: 'bold',
      color: theme.colors.text,
    },
    orderStatus: {
      fontSize: 14,
      fontWeight: '600',
    },
    orderDetails: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: theme.spacing.sm,
    },
    orderDetail: {
      flex: 1,
    },
    orderLabel: {
      fontSize: 12,
      color: theme.colors.textSecondary,
      marginBottom: theme.spacing.xs,
    },
    orderValue: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.colors.text,
    },
    cancelButton: {
      backgroundColor: theme.colors.error,
      borderRadius: 8,
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.md,
      alignSelf: 'flex-end',
    },
    cancelButtonText: {
      color: 'white',
      fontSize: 14,
      fontWeight: '600',
    },
    modal: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: 'rgba(0,0,0,0.5)',
    },
    modalContent: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.lg,
      width: '90%',
      maxWidth: 400,
    },
    modalTitle: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.lg,
      textAlign: 'center',
    },
    inputGroup: {
      marginBottom: theme.spacing.lg,
    },
    label: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.colors.text,
      marginBottom: theme.spacing.sm,
    },
    input: {
      backgroundColor: theme.colors.background,
      borderRadius: 8,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.md,
      fontSize: 16,
      color: theme.colors.text,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    typeSelector: {
      flexDirection: 'row',
      marginBottom: theme.spacing.lg,
    },
    typeButton: {
      flex: 1,
      paddingVertical: theme.spacing.md,
      alignItems: 'center',
      borderRadius: 8,
      marginHorizontal: theme.spacing.xs,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    selectedTypeButton: {
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    typeButtonText: {
      color: theme.colors.text,
      fontWeight: '600',
    },
    selectedTypeButtonText: {
      color: 'white',
    },
    modalButtons: {
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
    modalButton: {
      flex: 1,
      paddingVertical: theme.spacing.md,
      alignItems: 'center',
      borderRadius: 8,
      marginHorizontal: theme.spacing.xs,
    },
    cancelModalButton: {
      backgroundColor: theme.colors.border,
    },
    confirmModalButton: {
      backgroundColor: theme.colors.primary,
    },
    modalButtonText: {
      fontSize: 16,
      fontWeight: '600',
    },
    cancelModalButtonText: {
      color: theme.colors.text,
    },
    confirmModalButtonText: {
      color: 'white',
    },
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Trading</Text>
        <View style={styles.symbolSelector}>
          {symbols.map(symbol => (
            <TouchableOpacity
              key={symbol}
              style={[
                styles.symbolButton,
                selectedSymbol === symbol && styles.selectedSymbolButton
              ]}
              onPress={() => setSelectedSymbol(symbol)}
            >
              <Text style={[
                styles.symbolButtonText,
                selectedSymbol === symbol && styles.selectedSymbolButtonText
              ]}>
                {symbol}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.priceCard}>
          <Text style={styles.currentPrice}>
            {formatPrice(getCurrentPrice())}
          </Text>
          <Text style={styles.priceChange}>
            {selectedSymbol} - Prix actuel
          </Text>
        </View>

        <TouchableOpacity
          style={styles.orderButton}
          onPress={() => setIsOrderModalVisible(true)}
        >
          <Text style={styles.orderButtonText}>
            Passer un ordre
          </Text>
        </TouchableOpacity>

        <View style={styles.ordersSection}>
          <Text style={styles.sectionTitle}>Mes ordres</Text>
          {orders.length > 0 ? (
            orders.map(order => (
              <View key={order.id} style={styles.orderCard}>
                <View style={styles.orderHeader}>
                  <Text style={styles.orderSymbol}>{order.symbol}</Text>
                  <Text style={[
                    styles.orderStatus,
                    { color: getOrderStatusColor(order.status) }
                  ]}>
                    {getOrderStatusText(order.status)}
                  </Text>
                </View>
                <View style={styles.orderDetails}>
                  <View style={styles.orderDetail}>
                    <Text style={styles.orderLabel}>Type</Text>
                    <Text style={styles.orderValue}>
                      {order.side.toUpperCase()} {order.type.toUpperCase()}
                    </Text>
                  </View>
                  <View style={styles.orderDetail}>
                    <Text style={styles.orderLabel}>Quantité</Text>
                    <Text style={styles.orderValue}>{order.quantity}</Text>
                  </View>
                  {order.price && (
                    <View style={styles.orderDetail}>
                      <Text style={styles.orderLabel}>Prix</Text>
                      <Text style={styles.orderValue}>{formatPrice(order.price)}</Text>
                    </View>
                  )}
                </View>
                {order.status === 'pending' && (
                  <TouchableOpacity
                    style={styles.cancelButton}
                    onPress={() => handleCancelOrder(order.id)}
                  >
                    <Text style={styles.cancelButtonText}>Annuler</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))
          ) : (
            <View style={styles.orderCard}>
              <Text style={[styles.orderValue, { textAlign: 'center' }]}>
                Aucun ordre en cours
              </Text>
            </View>
          )}
        </View>
      </ScrollView>

      <Modal
        visible={isOrderModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setIsOrderModalVisible(false)}
      >
        <View style={styles.modal}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Nouvel ordre</Text>
            
            <View style={styles.typeSelector}>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  orderType === 'buy' && styles.selectedTypeButton
                ]}
                onPress={() => setOrderType('buy')}
              >
                <Text style={[
                  styles.typeButtonText,
                  orderType === 'buy' && styles.selectedTypeButtonText
                ]}>
                  ACHAT
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  orderType === 'sell' && styles.selectedTypeButton
                ]}
                onPress={() => setOrderType('sell')}
              >
                <Text style={[
                  styles.typeButtonText,
                  orderType === 'sell' && styles.selectedTypeButtonText
                ]}>
                  VENTE
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.typeSelector}>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  orderSide === 'market' && styles.selectedTypeButton
                ]}
                onPress={() => setOrderSide('market')}
              >
                <Text style={[
                  styles.typeButtonText,
                  orderSide === 'market' && styles.selectedTypeButtonText
                ]}>
                  MARCHÉ
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.typeButton,
                  orderSide === 'limit' && styles.selectedTypeButton
                ]}
                onPress={() => setOrderSide('limit')}
              >
                <Text style={[
                  styles.typeButtonText,
                  orderSide === 'limit' && styles.selectedTypeButtonText
                ]}>
                  LIMITE
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Quantité</Text>
              <TextInput
                style={styles.input}
                value={quantity}
                onChangeText={setQuantity}
                placeholder="0.00"
                keyboardType="numeric"
              />
            </View>

            {orderSide === 'limit' && (
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Prix limite</Text>
                <TextInput
                  style={styles.input}
                  value={price}
                  onChangeText={setPrice}
                  placeholder="0.00"
                  keyboardType="numeric"
                />
              </View>
            )}

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelModalButton]}
                onPress={() => setIsOrderModalVisible(false)}
              >
                <Text style={[styles.modalButtonText, styles.cancelModalButtonText]}>
                  Annuler
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.confirmModalButton]}
                onPress={handlePlaceOrder}
                disabled={isLoading}
              >
                <Text style={[styles.modalButtonText, styles.confirmModalButtonText]}>
                  {isLoading ? 'En cours...' : 'Confirmer'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

export default TradingScreen;