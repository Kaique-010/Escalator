import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthResponse, Usuario } from '../types';
import { baseApi } from './base.api';
import { apiPost } from '../api/typedClient';

class AuthApiService {
  // Autenticação (usando cliente tipado)
  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      // Logs de debug do payload sem expor senha
      console.log('[AUTH API] Login payload:', { username, password_present: !!password });

      const data = await apiPost('/api/token/', {
        username,
        password,
      } as any);

      const { access, refresh, user } = data as any;

      console.log('[AUTH API] Login sucesso:', {
        has_access: !!access,
        has_refresh: !!refresh,
        user_id: user?.id,
        username: user?.username,
      });

      // Salvar tokens no AsyncStorage
      await AsyncStorage.setItem('access_token', access);
      await AsyncStorage.setItem('refresh_token', refresh);
      await AsyncStorage.setItem('user_data', JSON.stringify(user));

      return data as AuthResponse;
    } catch (error: any) {
      // Logs de erro detalhado
      const status = error?.response?.status;
      const detail = error?.response?.data?.detail || error?.message;
      console.log('[AUTH API] Login falhou:', { status, detail });
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

      console.log('[AUTH API] Refresh token payload:', { has_refresh: !!refreshToken });
      const data = await apiPost('/api/token/refresh/', { refresh: refreshToken } as any);

      const { access } = data as any;
      await AsyncStorage.setItem('access_token', access);
      console.log('[AUTH API] Refresh token sucesso:', { has_access: !!access });

      return access as string;
    } catch (error: any) {
      const status = error?.response?.status;
      const detail = error?.response?.data?.detail || error?.message;
      console.log('[AUTH API] Refresh token falhou:', { status, detail });
      await this.logout();
      throw error as any;
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
    if (error?.response) {
      // Erro da API
      const message = error.response.data?.message || error.response.data?.detail || 'Erro na API';
      return new Error(message);
    } else if (error?.request) {
      // Erro de rede
      return new Error('Erro de conexão. Verifique sua internet.');
    } else {
      // Outro erro
      return new Error(error?.message || 'Erro desconhecido');
    }
  }
}

export default new AuthApiService();