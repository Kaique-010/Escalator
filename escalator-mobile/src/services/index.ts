// Exportações dos serviços de API
export { default as authApi } from './auth.api';
export { default as funcionariosApi } from './funcionarios.api';
export { default as escalasApi } from './escalas.api';
export { default as pontosApi } from './pontos.api';
export { default as bancoHorasApi } from './banco-horas.api';
export { default as dashboardApi } from './dashboard.api';

// Exportações da configuração base
export { baseApi, handleApiError } from './base.api';

// Exportação do arquivo original para compatibilidade
export * from './api';

// Tipos de erro da API
export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

// Configuração da API
export const API_CONFIG = {
  BASE_URL: 'http://127.0.0.1:8000/api',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// Utilitários para formatação de dados
export const formatters = {
  // Formatar tempo em horas e minutos
  formatTime: (horas: number, minutos: number): string => {
    const h = horas.toString().padStart(2, '0');
    const m = minutos.toString().padStart(2, '0');
    return `${h}:${m}`;
  },

  // Formatar data para exibição
  formatDate: (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  },

  // Formatar data e hora para exibição
  formatDateTime: (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
  },

  // Calcular diferença entre duas datas em minutos
  calculateMinutesDifference: (start: string, end: string): number => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    return Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60));
  },

  // Converter minutos para horas e minutos
  minutesToHoursAndMinutes: (totalMinutes: number): { horas: number; minutos: number } => {
    const horas = Math.floor(totalMinutes / 60);
    const minutos = totalMinutes % 60;
    return { horas, minutos };
  },
};