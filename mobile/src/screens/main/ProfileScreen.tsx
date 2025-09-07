// Écran du profil utilisateur
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const ProfileScreen = ({ navigation }: any) => {
  const { theme } = useTheme();
  const { user, updateUser, updatePreferences } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [preferences, setPreferences] = useState({
    currency: user?.preferences?.currency || 'USD',
    language: user?.preferences?.language || 'fr',
  });

  const handleSave = async () => {
    try {
      const success = await updateUser({ username, email });
      if (success) {
        Alert.alert('Succès', 'Profil mis à jour avec succès');
        setIsEditing(false);
      } else {
        Alert.alert('Erreur', 'Erreur lors de la mise à jour du profil');
      }
    } catch (error) {
      Alert.alert('Erreur', 'Erreur lors de la mise à jour du profil');
    }
  };

  const handleSavePreferences = async () => {
    try {
      const success = await updatePreferences(preferences);
      if (success) {
        Alert.alert('Succès', 'Préférences mises à jour avec succès');
      } else {
        Alert.alert('Erreur', 'Erreur lors de la mise à jour des préférences');
      }
    } catch (error) {
      Alert.alert('Erreur', 'Erreur lors de la mise à jour des préférences');
    }
  };

  const handleCancel = () => {
    setUsername(user?.username || '');
    setEmail(user?.email || '');
    setIsEditing(false);
  };

  const renderEditableField = (
    label: string,
    value: string,
    onChangeText: (text: string) => void,
    placeholder?: string,
    keyboardType?: any
  ) => (
    <View style={styles.fieldContainer}>
      <Text style={[styles.fieldLabel, { color: theme.colors.text }]}>
        {label}
      </Text>
      {isEditing ? (
        <TextInput
          style={[styles.input, { 
            backgroundColor: theme.colors.surface,
            color: theme.colors.text,
            borderColor: theme.colors.border
          }]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textSecondary}
          keyboardType={keyboardType}
        />
      ) : (
        <Text style={[styles.fieldValue, { color: theme.colors.text }]}>
          {value}
        </Text>
      )}
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
    profileSection: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.lg,
      marginBottom: theme.spacing.lg,
      alignItems: 'center',
    },
    avatar: {
      width: 100,
      height: 100,
      borderRadius: 50,
      backgroundColor: theme.colors.primary,
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: theme.spacing.md,
    },
    avatarText: {
      fontSize: 36,
      fontWeight: 'bold',
      color: 'white',
    },
    username: {
      fontSize: 24,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.xs,
    },
    email: {
      fontSize: 16,
      color: theme.colors.textSecondary,
    },
    editButton: {
      backgroundColor: theme.colors.primary,
      borderRadius: 8,
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.lg,
      marginTop: theme.spacing.md,
    },
    editButtonText: {
      color: 'white',
      fontSize: 16,
      fontWeight: '600',
    },
    section: {
      backgroundColor: theme.colors.surface,
      borderRadius: 12,
      padding: theme.spacing.lg,
      marginBottom: theme.spacing.lg,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    fieldContainer: {
      marginBottom: theme.spacing.lg,
    },
    fieldLabel: {
      fontSize: 16,
      fontWeight: '600',
      marginBottom: theme.spacing.sm,
    },
    fieldValue: {
      fontSize: 16,
      paddingVertical: theme.spacing.sm,
    },
    input: {
      borderWidth: 1,
      borderRadius: 8,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      fontSize: 16,
    },
    preferencesContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing.lg,
    },
    preferenceLabel: {
      fontSize: 16,
      color: theme.colors.text,
    },
    preferenceValue: {
      fontSize: 16,
      color: theme.colors.textSecondary,
    },
    actionButtons: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginTop: theme.spacing.lg,
    },
    button: {
      flex: 1,
      paddingVertical: theme.spacing.md,
      borderRadius: 8,
      alignItems: 'center',
      marginHorizontal: theme.spacing.xs,
    },
    saveButton: {
      backgroundColor: theme.colors.primary,
    },
    cancelButton: {
      backgroundColor: theme.colors.border,
    },
    buttonText: {
      fontSize: 16,
      fontWeight: '600',
    },
    saveButtonText: {
      color: 'white',
    },
    cancelButtonText: {
      color: theme.colors.text,
    },
    statsContainer: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginTop: theme.spacing.lg,
      paddingTop: theme.spacing.lg,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
    },
    stat: {
      alignItems: 'center',
    },
    statValue: {
      fontSize: 20,
      fontWeight: 'bold',
      color: theme.colors.text,
      marginBottom: theme.spacing.xs,
    },
    statLabel: {
      fontSize: 14,
      color: theme.colors.textSecondary,
    },
  });

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Profil</Text>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.profileSection}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </Text>
          </View>
          <Text style={styles.username}>
            {isEditing ? username : user?.username || 'Utilisateur'}
          </Text>
          <Text style={styles.email}>
            {isEditing ? email : user?.email || 'email@example.com'}
          </Text>
          {!isEditing && (
            <TouchableOpacity
              style={styles.editButton}
              onPress={() => setIsEditing(true)}
            >
              <Text style={styles.editButtonText}>Modifier le profil</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Informations personnelles</Text>
          {renderEditableField(
            'Nom d\'utilisateur',
            username,
            setUsername,
            'Votre nom d\'utilisateur'
          )}
          {renderEditableField(
            'Email',
            email,
            setEmail,
            'votre@email.com',
            'email-address'
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Préférences</Text>
          <View style={styles.preferencesContainer}>
            <Text style={styles.preferenceLabel}>Devise</Text>
            <Text style={styles.preferenceValue}>{preferences.currency}</Text>
          </View>
          <View style={styles.preferencesContainer}>
            <Text style={styles.preferenceLabel}>Langue</Text>
            <Text style={styles.preferenceValue}>
              {preferences.language === 'fr' ? 'Français' : 'English'}
            </Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Statistiques</Text>
          <View style={styles.statsContainer}>
            <View style={styles.stat}>
              <Text style={styles.statValue}>0</Text>
              <Text style={styles.statLabel}>Ordres exécutés</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statValue}>0</Text>
              <Text style={styles.statLabel}>Arbitrages</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statValue}>0%</Text>
              <Text style={styles.statLabel}>Profit</Text>
            </View>
          </View>
        </View>

        {isEditing && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={handleCancel}
            >
              <Text style={[styles.buttonText, styles.cancelButtonText]}>
                Annuler
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.saveButton]}
              onPress={handleSave}
            >
              <Text style={[styles.buttonText, styles.saveButtonText]}>
                Sauvegarder
              </Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

export default ProfileScreen;