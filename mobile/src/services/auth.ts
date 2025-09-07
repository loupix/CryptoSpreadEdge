// Service d'authentification pour l'application mobile
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';
import { apiService } from './api';
import { User, LoginRequest, RegisterRequest } from '../types';

class AuthService {
  private currentUser: User | null = null;
  private isInitialized = false;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Vérifier si l'utilisateur est déjà connecté
      const credentials = await Keychain.getInternetCredentials('cryptospreadedge_auth');
      
      if (credentials && credentials.password) {
        // Token trouvé, vérifier s'il est encore valide
        const response = await apiService.getCurrentUser();
        
        if (response.success && response.data) {
          this.currentUser = response.data;
          this.isInitialized = true;
          return;
        } else {
          // Token invalide, essayer de le rafraîchir
          const refreshResponse = await apiService.refreshToken();
          
          if (refreshResponse.success && refreshResponse.data) {
            this.currentUser = refreshResponse.data.user;
            this.isInitialized = true;
            return;
          }
        }
      }

      // Aucune authentification valide trouvée
      this.currentUser = null;
      this.isInitialized = true;
    } catch (error) {
      console.error('Erreur initialisation auth:', error);
      this.currentUser = null;
      this.isInitialized = true;
    }
  }

  async login(credentials: LoginRequest): Promise<{ success: boolean; user?: User; error?: string }> {
    try {
      const response = await apiService.login(credentials);
      
      if (response.success && response.data) {
        this.currentUser = response.data.user;
        
        // Sauvegarder les credentials de manière sécurisée
        await Keychain.setInternetCredentials(
          'cryptospreadedge_auth',
          credentials.email,
          response.data.token
        );
        
        return { success: true, user: this.currentUser };
      } else {
        return { success: false, error: response.error || 'Erreur de connexion' };
      }
    } catch (error) {
      console.error('Erreur login:', error);
      return { success: false, error: 'Erreur de connexion' };
    }
  }

  async register(userData: RegisterRequest): Promise<{ success: boolean; user?: User; error?: string }> {
    try {
      const response = await apiService.register(userData);
      
      if (response.success && response.data) {
        this.currentUser = response.data.user;
        
        // Sauvegarder les credentials de manière sécurisée
        await Keychain.setInternetCredentials(
          'cryptospreadedge_auth',
          userData.email,
          response.data.token
        );
        
        return { success: true, user: this.currentUser };
      } else {
        return { success: false, error: response.error || 'Erreur d\'inscription' };
      }
    } catch (error) {
      console.error('Erreur register:', error);
      return { success: false, error: 'Erreur d\'inscription' };
    }
  }

  async logout(): Promise<void> {
    try {
      await apiService.logout();
    } catch (error) {
      console.error('Erreur logout:', error);
    } finally {
      this.currentUser = null;
      
      // Supprimer les credentials
      await Keychain.resetInternetCredentials('cryptospreadedge_auth');
      await AsyncStorage.removeItem('auth_token');
      await AsyncStorage.removeItem('refresh_token');
    }
  }

  async refreshToken(): Promise<boolean> {
    try {
      const response = await apiService.refreshToken();
      
      if (response.success && response.data) {
        this.currentUser = response.data.user;
        return true;
      } else {
        // Token invalide, déconnecter l'utilisateur
        await this.logout();
        return false;
      }
    } catch (error) {
      console.error('Erreur refresh token:', error);
      await this.logout();
      return false;
    }
  }

  getCurrentUser(): User | null {
    return this.currentUser;
  }

  isAuthenticated(): boolean {
    return this.currentUser !== null && this.currentUser.isAuthenticated;
  }

  async updateUser(user: Partial<User>): Promise<boolean> {
    try {
      if (this.currentUser) {
        this.currentUser = { ...this.currentUser, ...user };
        return true;
      }
      return false;
    } catch (error) {
      console.error('Erreur update user:', error);
      return false;
    }
  }

  async updatePreferences(preferences: Partial<any>): Promise<boolean> {
    try {
      const response = await apiService.updateUserPreferences(preferences);
      
      if (response.success && response.data) {
        this.currentUser = response.data;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Erreur update preferences:', error);
      return false;
    }
  }

  isInitialized(): boolean {
    return this.isInitialized;
  }
}

export const authService = new AuthService();
export default authService;