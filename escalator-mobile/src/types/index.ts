// Tipos para o sistema de escalas
import type { components } from '../api/types';

// Mantemos o tipo de Usuario e respostas de auth conforme usado no app
export interface Usuario {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active?: boolean;
  is_staff?: boolean;
}

// Alinhamos tipos do domínio aos esquemas OpenAPI gerados
export type Funcionario = components['schemas']['Funcionario'];
export type EscalaPredefinida = components['schemas']['EscalaPredefinida'];
export type Escala = components['schemas']['Escala'];
export type Ponto = components['schemas']['Ponto'];
export type BancoHoras = components['schemas']['BancoHoras'];

export interface AuthResponse {
  access: string;
  refresh: string;
  user: Usuario;
}

// Tipos específicos do app (não presentes no OpenAPI)
export interface DashboardData {
  escala_hoje?: Escala;
  pontos_hoje: Ponto[];
  banco_horas_atual: BancoHoras | null;
  alertas: string[];
  horas_trabalhadas_semana: number;
}

export interface ApiError {
  message: string;
  details?: any;
}