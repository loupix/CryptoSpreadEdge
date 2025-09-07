// Écran des paramètres
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const SettingsScreen = ({ navigation }: any) => {
  const { theme, isDarkMode, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [priceAlertsEnabled, setPriceAlertsEnabled] = useState(true);
  const [tradeAlertsEnabled, setTradeAlertsEnabled] = useState(true);

  const handleLogout = () => {
    Alert.alert(
      'Déconnexion',
      'Êtes-vous sûr de vouloir vous déconnecter ?',
      [
        { text: 'Annuler', style: 'cancel' },
        { 
          text: 'Déconnexion', 
          style: 'destructive',
          onPress: logout
        }
      ]
    );
  };

  const handleClearCache = () => {
    Alert.alert(
      'Vider le cache',
      'Voulez-vous vider le cache de l\'application ?',
      [
        { text: 'Annuler', style: 'cancel' },
        { 
          text: 'Vider', 
          onPress: () => {
            // TODO: Implémenter la logique de vidage du cache
            Alert.alert('Succès', 'Cache vidé avec succès');
          }
        }
      ]
    );
  };

  const handleExportData = () => {
    Alert.alert(
      'Exporter les données',
      'Voulez-vous exporter vos données de trading ?',
      [
        { text: 'Annuler', style: 'cancel' },
        { 
          text: 'Exporter', 
          onPress: () => {
            // TODO: Implémenter l'export des données
            Alert.alert('Succès', 'Données exportées avec succès');
          }
        }
      ]
    );
  };

  const renderSettingItem = (
    icon: string,
    title: string,
    subtitle?: string,
    onPress?: () => void,
    rightComponent?: React.ReactNode
  ) => (
    <TouchableOpacity
      style={styles.settingItem}
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.settingLeft}>
        <View style={[styles.iconContainer, { backgroundColor: theme.colors.primary + '20' }]}>
          <Icon name={icon} size={24} color={theme.colors.primary} />
        </View>
        <View style={styles.settingText}>
          <Text style={[styles.settingTitle, { color: theme.colors.text }]}>
            {title}
          </Text>
          {subtitle && (
            <Text style={[styles.settingSubtitle, { color: theme.colors.textSecondary }]}>
              {subtitle}
            </Text>
          )}
        </View>
      </View>
      {rightComponent || (onPress && (
        <Icon name="chevron-right" size={24} color={theme.colors.textSecondary} />
      ))}
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
    },
    content: {
      flex: 1,
    },
    section: {
      marginTop: theme.spacing.lg,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
      paddingHorizontal: theme.spacing.lg,
    },
    settingItem: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: theme.spacing.lg,
      paddingVertical: theme.spacing.md,
      backgroundColor: theme.colors.surface,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    settingLeft: {
      flexDirection: 'row',
      alignItems: 'center',
      flex: 1,
    },
    iconContainer: {
      width: 40,
      height: 40,
      borderRadius: 20,
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: theme.spacing.md,
    },
    settingText: {
      flex: 1,
    },
    settingTitle: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: theme.spacing.xs,
    },
    settingSubtitle: {
      fontSize: 14,
    },
    userSection: {
      backgroundColor: theme.colors.surface,
      padding: theme.spacing.lg,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
    },
    userInfo: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: theme.spacing.md,
    },
    avatar: {
      width: 60,
      height: 60,
      borderRadius: 30,
      backgroundColor: theme.colors.primary,
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: theme.spacing.md,
    },
    avatarText: {
      fontSize: 24,
      fontWeight: 'bold',
      color: 'white',
    },
    userDetails: {
      flex: 1,
    },
    username: {
      fontSize: 18,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.xs,
    },
    userEmail: {
      fontSize: 14,
      color: theme.colors.textSecondary,
    },
    logoutButton: {
      backgroundColor: theme.colors.error,
      borderRadius: 8,
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.md,
      alignSelf: 'flex-start',
    },
    logoutButtonText: {
      color: 'white',
      fontSize: 14,
      fontWeight: '600',
    },
    versionInfo: {
      alignItems: 'center',
      padding: theme.spacing.lg,
    },
    versionText: {
      fontSize: 14,
      color: theme.colors.textSecondary,
    },
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Paramètres</Text>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.userSection}>
          <View style={styles.userInfo}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </Text>
            </View>
            <View style={styles.userDetails}>
              <Text style={styles.username}>
                {user?.username || 'Utilisateur'}
              </Text>
              <Text style={styles.userEmail}>
                {user?.email || 'email@example.com'}
              </Text>
            </View>
          </View>
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutButtonText}>Se déconnecter</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Apparence</Text>
          {renderSettingItem(
            'palette',
            'Mode sombre',
            isDarkMode ? 'Activé' : 'Désactivé',
            undefined,
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor={isDarkMode ? 'white' : theme.colors.textSecondary}
            />
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          {renderSettingItem(
            'notifications',
            'Notifications push',
            'Recevoir des notifications',
            undefined,
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor={notificationsEnabled ? 'white' : theme.colors.textSecondary}
            />
          )}
          {renderSettingItem(
            'trending-up',
            'Alertes de prix',
            'Notifications de changement de prix',
            undefined,
            <Switch
              value={priceAlertsEnabled}
              onValueChange={setPriceAlertsEnabled}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor={priceAlertsEnabled ? 'white' : theme.colors.textSecondary}
            />
          )}
          {renderSettingItem(
            'swap-horiz',
            'Alertes de trading',
            'Notifications d\'ordres et d\'arbitrage',
            undefined,
            <Switch
              value={tradeAlertsEnabled}
              onValueChange={setTradeAlertsEnabled}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor={tradeAlertsEnabled ? 'white' : theme.colors.textSecondary}
            />
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Données</Text>
          {renderSettingItem(
            'person',
            'Profil',
            'Gérer votre profil',
            () => navigation.navigate('Profile')
          )}
          {renderSettingItem(
            'download',
            'Exporter les données',
            'Télécharger vos données de trading',
            handleExportData
          )}
          {renderSettingItem(
            'delete',
            'Vider le cache',
            'Supprimer les données temporaires',
            handleClearCache
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Support</Text>
          {renderSettingItem(
            'help',
            'Aide',
            'Centre d\'aide et FAQ'
          )}
          {renderSettingItem(
            'email',
            'Nous contacter',
            'Support technique'
          )}
          {renderSettingItem(
            'info',
            'À propos',
            'Version et informations'
          )}
        </View>

        <View style={styles.versionInfo}>
          <Text style={styles.versionText}>
            CryptoSpreadEdge Mobile v1.0.0
          </Text>
        </View>
      </ScrollView>
    </View>
  );
};

export default SettingsScreen;