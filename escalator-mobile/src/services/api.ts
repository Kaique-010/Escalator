import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthResponse, Usuario, Funcionario, Escala, Ponto, BancoHoras, DashboardData } from '../types';
import { apiGet, apiPost } from '../api/typedClient';

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
        // Log de request
        try {
          console.log('[API] Request:', { url: config.url, method: config.method, has_auth: !!token });
        } catch {}
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Interceptor para lidar com respostas e renovar token
    this.api.interceptors.response.use(
      (response) => {
        try {
          console.log('[API] Response:', { url: response.config?.url, status: response.status });
        } catch {}
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = await AsyncStorage.getItem('refresh_token');
            console.log('[API] 401 interceptado, tentando refresh:', { has_refresh: !!refreshToken });
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
                refresh: refreshToken,
              });

              const { access } = response.data;
              await AsyncStorage.setItem('access_token', access);
              console.log('[API] Refresh sucesso:', { has_access: !!access });

              originalRequest.headers.Authorization = `Bearer ${access}`;
              return this.api(originalRequest);
            } else {
              // Não há refresh token, fazer logout
              await this.logout();
              throw new Error('Sessão expirada. Faça login novamente.');
            }
          } catch (refreshError) {
            // Token refresh falhou, fazer logout
            await this.logout();
            console.log('[API] Refresh falhou:', { detail: (refreshError as any)?.message });
            throw new Error('Sessão expirada. Faça login novamente.');
          }
        }

        try {
          console.log('[API] Response erro:', { url: originalRequest?.url, status: error.response?.status });
        } catch {}
        return Promise.reject(error);
      }
    );
  }

  // Autenticação
  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      console.log('[API] Login payload:', { username, password_present: !!password });
      const response: AxiosResponse<AuthResponse> = await this.api.post('/token/', {
        username,
        password,
      });

      const { access, refresh, user } = response.data;

      console.log('[API] Login sucesso:', { status: response.status, user_id: user?.id, username: user?.username });

      // Salvar tokens no AsyncStorage
      await AsyncStorage.setItem('access_token', access);
      await AsyncStorage.setItem('refresh_token', refresh);
      await AsyncStorage.setItem('user_data', JSON.stringify(user));

      return response.data;
    } catch (error: any) {
      console.log('[API] Login falhou:', { status: error?.response?.status, detail: error?.response?.data?.detail || error?.message });
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
      // Primeiro tenta obter do AsyncStorage
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        const user = JSON.parse(userData);
        
        // Verifica se o usuário tem dados do funcionário
        if (user.funcionario) {
          return user;
        }
        
        // Se não tem dados do funcionário, busca na API
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          const response = await this.api.get('/funcionarios/me/', {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          
          // Atualiza os dados do usuário com informações do funcionário
          const updatedUser = {
            ...user,
            funcionario: response.data
          };
          
          // Salva os dados atualizados
          await AsyncStorage.setItem('user_data', JSON.stringify(updatedUser));
          return updatedUser;
        }
      }
      
      return null;
    } catch (error) {
      console.error('Erro ao obter usuário atual:', error);
      return null;
    }
  }

  // Dashboard (custom)
  async getDashboardData(): Promise<DashboardData> {
    try {
      const response: AxiosResponse<DashboardData> = await this.api.get('/relatorios/dashboard/');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Alias para compatibilidade
  async getDashboard(): Promise<DashboardData> {
    return this.getDashboardData();
  }

  // Funcionários (cliente tipado)
  async getFuncionario(id: string): Promise<Funcionario> {
    try {
      const data = await apiGet('/api/funcionarios/{id}/', { path: { id: Number(id) } });
      return data as Funcionario;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Escalas (cliente tipado)
  async getEscalas(funcionarioId?: string, dataInicio?: string, dataFim?: string): Promise<Escala[]> {
    try {
      const data = await apiGet('/api/escalas/', {
        query: {
          funcionario: funcionarioId ? Number(funcionarioId) : undefined,
          // extras fora do schema OpenAPI
          data_inicio: dataInicio,
          data_fim: dataFim,
        } as any,
      });
      return (data as any).results ?? [];
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

  // Pontos (cliente tipado)
  async registrarPonto(
    funcionarioId: string,
    tipoRegistro: 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim',
    localizacao?: { latitude: number; longitude: number },
    observacoes?: string
  ): Promise<Ponto> {
    try {
      const data = await apiPost('/api/pontos/', {
        funcionario: Number(funcionarioId),
        tipo_registro: tipoRegistro as any,
        timestamp: new Date().toISOString(),
        localizacao_lat: localizacao?.latitude ?? null,
        localizacao_lng: localizacao?.longitude ?? null,
        observacoes,
      } as any);
      return data as Ponto;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getPontos(funcionarioId?: string, dataInicio?: string, dataFim?: string): Promise<Ponto[]> {
    try {
      const data = await apiGet('/api/pontos/', {
        query: {
          funcionario: funcionarioId ? Number(funcionarioId) : undefined,
          // extras fora do schema OpenAPI
          data_inicio: dataInicio,
          data_fim: dataFim,
        } as any,
      });
      return (data as any).results ?? [];
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

  // Banco de Horas (cliente tipado)
  async getBancoHoras(funcionarioId: string): Promise<BancoHoras[]> {
    try {
      const data = await apiGet('/api/banco-horas/', {
        query: { funcionario: Number(funcionarioId) } as any,
      });
      return (data as any).results ?? [];
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getBancoHorasAtual(funcionarioId: string): Promise<BancoHoras | null> {
    try {
      const lista = await this.getBancoHoras(funcionarioId);
      return lista.length > 0 ? lista[0] : null;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  private handleError(error: any): Error {
    if (error?.response) {
      const message = error.response.data?.message || error.response.data?.detail || 'Erro na API';
      return new Error(message);
    } else if (error?.request) {
      return new Error('Erro de conexão. Verifique sua internet.');
    } else {
      return new Error(error?.message || 'Erro desconhecido');
    }
  }

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