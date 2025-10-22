import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configuração base da API
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Instância base do axios
export const baseApi: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token automaticamente
baseApi.interceptors.request.use(
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
baseApi.interceptors.response.use(
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
          return baseApi(originalRequest);
        }
      } catch (refreshError) {
        // Token refresh falhou, limpar storage
        await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user_data']);
        throw refreshError;
      }
    }

    return Promise.reject(error);
  }
);

// Função helper para tratamento de erros
export const handleApiError = (error: any): Error => {
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
};