import axios, { AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthResponse, Usuario } from '../types';
import { baseApi } from './base.api';

class AuthApiService {
  // Autenticação
  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      const response: AxiosResponse<AuthResponse> = await baseApi.post('/token/', {
        username,
        password,
      });

      const { access, refresh, user } = response.data;

      // Salvar tokens no AsyncStorage
      await AsyncStorage.setItem('access_token', access);
      await AsyncStorage.setItem('refresh_token', refresh);
      await AsyncStorage.setItem('user_data', JSON.stringify(user));

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async logout(): Promise<void> {
    try {
      // Remover tokens do AsyncStorage
      await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user_data']);
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  }

  async getCurrentUser(): Promise<Usuario | null> {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      return null;
    }
  }

  async refreshToken(): Promise<string> {
    try {
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(`${baseApi.defaults.baseURL}/token/refresh/`, {
        refresh: refreshToken,
      });

      const { access } = response.data;
      await AsyncStorage.setItem('access_token', access);

      return access;
    } catch (error) {
      await this.logout();
      throw error;
    }
  }

  // Verificar se está autenticado
  async isAuthenticated(): Promise<boolean> {
    try {
      const token = await AsyncStorage.getItem('access_token');
      return !!token;
    } catch (error) {
      return false;
    }
  }

  // Tratamento de erros
  private handleError(error: any): Error {
    if (error.response) {
      // Erro da API
      const message = error.response.data?.message || error.response.data?.detail || 'Erro na API';
      return new Error(message);
    } else if (error.request) {
      // Erro de rede
      return new Error('Erro de conexão. Verifique sua internet.');
    } else {
      // Outro erro
      return new Error(error.message || 'Erro desconhecido');
    }
  }
}

export default new AuthApiService();