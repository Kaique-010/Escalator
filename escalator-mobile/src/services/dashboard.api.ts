import { AxiosResponse } from 'axios';
import { baseApi, handleApiError } from './base.api';

interface DashboardData {
  funcionarios_ativos: number;
  funcionarios_trabalhando: number;
  pontos_hoje: number;
  horas_trabalhadas_hoje: number;
  funcionarios_recentes: Array<{
    id: string;
    nome: string;
    ultimo_ponto: string;
    status: 'trabalhando' | 'pausa' | 'saiu';
  }>;
  estatisticas_semanais: {
    total_horas: number;
    media_diaria: number;
    dias_trabalhados: number;
  };
  alertas: Array<{
    tipo: 'atraso' | 'falta' | 'hora_extra';
    funcionario: string;
    mensagem: string;
    data: string;
  }>;
}

interface RelatorioPeriodo {
  periodo: {
    inicio: string;
    fim: string;
  };
  funcionarios: Array<{
    id: string;
    nome: string;
    total_horas: number;
    dias_trabalhados: number;
    faltas: number;
    atrasos: number;
    horas_extras: number;
  }>;
  resumo: {
    total_funcionarios: number;
    total_horas_trabalhadas: number;
    media_horas_por_funcionario: number;
    total_faltas: number;
    total_atrasos: number;
  };
}

class DashboardApiService {
  // Obter dados do dashboard
  async getDashboardData(): Promise<DashboardData> {
    try {
      const response: AxiosResponse<DashboardData> = await baseApi.get('/dashboard/');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter dados do dashboard para um funcionário específico
  async getDashboardFuncionario(funcionarioId: string): Promise<{
    escala_hoje: any;
    pontos_hoje: any[];
    saldo_banco_horas: { horas: number; minutos: number };
    horas_trabalhadas_mes: number;
    status_atual: 'trabalhando' | 'pausa' | 'fora';
    proximo_ponto: 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim';
  }> {
    try {
      const response = await baseApi.get(`/dashboard/funcionario/${funcionarioId}/`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter estatísticas gerais
  async getEstatisticas(periodo?: {
    data_inicio: string;
    data_fim: string;
  }): Promise<{
    total_funcionarios: number;
    funcionarios_ativos: number;
    total_pontos: number;
    horas_trabalhadas: number;
    media_horas_por_funcionario: number;
    funcionarios_com_mais_horas: Array<{
      funcionario: string;
      nome: string;
      horas: number;
    }>;
  }> {
    try {
      const params = periodo ? {
        data_inicio: periodo.data_inicio,
        data_fim: periodo.data_fim
      } : {};

      const response = await baseApi.get('/dashboard/estatisticas/', { params });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter relatório de frequência
  async getRelatorioFrequencia(params: {
    data_inicio: string;
    data_fim: string;
    funcionario?: string;
  }): Promise<RelatorioPeriodo> {
    try {
      const response = await baseApi.get('/dashboard/relatorio-frequencia/', { params });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter funcionários em tempo real
  async getFuncionariosTempoReal(): Promise<Array<{
    id: string;
    nome: string;
    status: 'trabalhando' | 'pausa' | 'fora';
    ultimo_ponto: string;
    tempo_trabalhado_hoje: number;
    localizacao?: {
      latitude: number;
      longitude: number;
    };
  }>> {
    try {
      const response = await baseApi.get('/dashboard/tempo-real/');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter alertas do sistema
  async getAlertas(params?: {
    tipo?: 'atraso' | 'falta' | 'hora_extra';
    data_inicio?: string;
    data_fim?: string;
    funcionario?: string;
  }): Promise<Array<{
    id: string;
    tipo: 'atraso' | 'falta' | 'hora_extra';
    funcionario: string;
    funcionario_nome: string;
    mensagem: string;
    data: string;
    resolvido: boolean;
  }>> {
    try {
      const response = await baseApi.get('/dashboard/alertas/', { params });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Marcar alerta como resolvido
  async resolverAlerta(alertaId: string): Promise<void> {
    try {
      await baseApi.patch(`/dashboard/alertas/${alertaId}/`, { resolvido: true });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter resumo semanal
  async getResumoSemanal(funcionarioId?: string): Promise<{
    semana_atual: {
      inicio: string;
      fim: string;
      horas_trabalhadas: number;
      dias_trabalhados: number;
      meta_horas: number;
    };
    comparacao_semana_anterior: {
      diferenca_horas: number;
      diferenca_dias: number;
      percentual_mudanca: number;
    };
  }> {
    try {
      const params = funcionarioId ? { funcionario: funcionarioId } : {};
      const response = await baseApi.get('/dashboard/resumo-semanal/', { params });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new DashboardApiService();