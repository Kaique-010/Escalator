import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthResponse, Usuario, Funcionario, Escala, Ponto, BancoHoras, DashboardData } from '../types';

// Configuração base da API
const API_BASE_URL = 'http://127.0.0.1:8000/api';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para adicionar token automaticamente
    this.api.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Interceptor para lidar com respostas e renovar token
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = await AsyncStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
                refresh: refreshToken,
              });

              const { access } = response.data;
              await AsyncStorage.setItem('access_token', access);

              originalRequest.headers.Authorization = `Bearer ${access}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // Token refresh falhou, fazer logout
            await this.logout();
            throw refreshError;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Autenticação
  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      const response: AxiosResponse<AuthResponse> = await this.api.post('/token/', {
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

  // Dashboard
  async getDashboardData(): Promise<DashboardData> {
    try {
      const response: AxiosResponse<DashboardData> = await this.api.get('/relatorios/dashboard/');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Funcionários
  async getFuncionario(id: string): Promise<Funcionario> {
    try {
      const response: AxiosResponse<Funcionario> = await this.api.get(`/funcionarios/${id}/`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Escalas
  async getEscalas(funcionarioId?: string, dataInicio?: string, dataFim?: string): Promise<Escala[]> {
    try {
      const params = new URLSearchParams();
      if (funcionarioId) params.append('funcionario', funcionarioId);
      if (dataInicio) params.append('data_inicio', dataInicio);
      if (dataFim) params.append('data_fim', dataFim);

      const response: AxiosResponse<{ results: Escala[] }> = await this.api.get(
        `/escalas/?${params.toString()}`
      );
      return response.data.results;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getEscalaHoje(funcionarioId: string): Promise<Escala | null> {
    try {
      const hoje = new Date().toISOString().split('T')[0];
      const escalas = await this.getEscalas(funcionarioId, hoje, hoje);
      return escalas.length > 0 ? escalas[0] : null;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Pontos
  async registrarPonto(
    funcionarioId: string,
    tipoRegistro: 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim',
    localizacao?: { latitude: number; longitude: number },
    observacoes?: string
  ): Promise<Ponto> {
    try {
      const response: AxiosResponse<Ponto> = await this.api.post('/pontos/', {
        funcionario: funcionarioId,
        tipo_registro: tipoRegistro,
        timestamp: new Date().toISOString(),
        localizacao,
        observacoes,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getPontos(funcionarioId?: string, dataInicio?: string, dataFim?: string): Promise<Ponto[]> {
    try {
      const params = new URLSearchParams();
      if (funcionarioId) params.append('funcionario', funcionarioId);
      if (dataInicio) params.append('data_inicio', dataInicio);
      if (dataFim) params.append('data_fim', dataFim);

      const response: AxiosResponse<{ results: Ponto[] }> = await this.api.get(
        `/pontos/?${params.toString()}`
      );
      return response.data.results;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getPontosHoje(funcionarioId: string): Promise<Ponto[]> {
    try {
      const hoje = new Date().toISOString().split('T')[0];
      return await this.getPontos(funcionarioId, hoje, hoje);
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Banco de Horas
  async getBancoHoras(funcionarioId: string): Promise<BancoHoras[]> {
    try {
      const response: AxiosResponse<{ results: BancoHoras[] }> = await this.api.get(
        `/banco-horas/?funcionario=${funcionarioId}`
      );
      return response.data.results;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getBancoHorasAtual(funcionarioId: string): Promise<BancoHoras | null> {
    try {
      const bancoHoras = await this.getBancoHoras(funcionarioId);
      // Retorna o mais recente
      return bancoHoras.length > 0 ? bancoHoras[0] : null;
    } catch (error) {
      throw this.handleError(error);
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

  // Verificar se está autenticado
  async isAuthenticated(): Promise<boolean> {
    try {
      const token = await AsyncStorage.getItem('access_token');
      return !!token;
    } catch (error) {
      return false;
    }
  }
}

export default new ApiService();