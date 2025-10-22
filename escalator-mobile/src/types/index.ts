// Tipos para o sistema de escalas
export interface Usuario {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  funcionario?: Funcionario;
}

export interface Funcionario {
  id: string;
  usuario: Usuario;
  nome: string;
  matricula: string;
  cpf: string;
  email: string;
  telefone: string;
  cargo: string;
  setor: string;
  salario: number;
  ativo: boolean;
  created_at: string;
}

export interface Contrato {
  id: string;
  funcionario: string;
  carga_diaria_max: number;
  carga_semanal_max: number;
  extra_diaria_cap: number;
  banco_horas_prazo_meses: number;
  permite_12x36: boolean;
  vigencia_inicio: string;
  vigencia_fim?: string;
}

export interface EscalaPredefinida {
  id: string;
  nome: string;
  descricao: string;
  horas_trabalho: number;
  horas_descanso: number;
}

export interface Escala {
  id: string;
  funcionario: string;
  data: string;
  hora_inicio: string;
  hora_fim: string;
  pausa_minutos: number;
  tipo_escala: string;
  descanso: boolean;
  created_at: string;
}

export interface Ponto {
  id: string;
  funcionario: string;
  escala?: string;
  timestamp: string;
  tipo_registro: 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim';
  localizacao?: {
    latitude: number;
    longitude: number;
  };
  validado: boolean;
  observacoes?: string;
  created_at: string;
}

export interface BancoHoras {
  id: string;
  funcionario: string;
  data_referencia: string;
  credito_minutos: number;
  debito_minutos: number;
  saldo_minutos: number;
  data_vencimento?: string;
  compensado: boolean;
  observacoes?: string;
  created_at: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: Usuario;
}

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