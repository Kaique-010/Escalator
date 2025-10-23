import { Escala } from '../types';
import { handleApiError } from './base.api';
import { apiGet, apiPost, apiPatch, apiDelete } from '../api/typedClient';

class EscalasApiService {
  // Listar escalas (cliente tipado)
  async getEscalas(params?: {
    funcionario?: string;
    data_inicio?: string; // suportado no backend, pode não estar no schema
    data_fim?: string; // suportado no backend, pode não estar no schema
    tipo_escala?: string;
    page?: number;
  }): Promise<{ results: Escala[]; count: number; next: string | null; previous: string | null }> {
    try {
      const data = await apiGet('/api/escalas/', {
        query: {
          funcionario: params?.funcionario ? Number(params.funcionario) : undefined,
          tipo_escala: params?.tipo_escala as any,
          page: params?.page,
          // extras fora do schema OpenAPI
          data_inicio: params?.data_inicio,
          data_fim: params?.data_fim,
        } as any,
      });
      return data as any;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter escala por ID
  async getEscala(id: string): Promise<Escala> {
    try {
      const data = await apiGet('/api/escalas/{id}/', { path: { id: Number(id) } });
      return data as Escala;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter escala de hoje para um funcionário
  async getEscalaHoje(funcionarioId: string): Promise<Escala | null> {
    try {
      const hoje = new Date().toISOString().split('T')[0];
      const response = await this.getEscalas({
        funcionario: funcionarioId,
        data_inicio: hoje,
        data_fim: hoje,
      });
      return response.results.length > 0 ? response.results[0] : null;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Criar escala
  async createEscala(escala: Omit<Escala, 'id' | 'created_at'>): Promise<Escala> {
    try {
      const data = await apiPost('/api/escalas/', escala as any);
      return data as Escala;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar escala (PATCH)
  async updateEscala(id: string, escala: Partial<Escala>): Promise<Escala> {
    try {
      const data = await apiPatch('/api/escalas/{id}/', escala as any, { path: { id: Number(id) } });
      return data as Escala;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar escala
  async deleteEscala(id: string): Promise<void> {
    try {
      await apiDelete('/api/escalas/{id}/', { path: { id: Number(id) } });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter escalas da semana
  async getEscalasSemana(funcionarioId: string, dataInicio: string): Promise<Escala[]> {
    try {
      const dataFimDate = new Date(dataInicio);
      dataFimDate.setDate(dataFimDate.getDate() + 6);
      const dataFim = dataFimDate.toISOString().split('T')[0];

      const response = await this.getEscalas({
        funcionario: funcionarioId,
        data_inicio: dataInicio,
        data_fim: dataFim,
      });

      return response.results;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter escalas do mês
  async getEscalasMes(funcionarioId: string, ano: number, mes: number): Promise<Escala[]> {
    try {
      const dataInicio = new Date(ano, mes - 1, 1).toISOString().split('T')[0];
      const dataFim = new Date(ano, mes, 0).toISOString().split('T')[0];

      const response = await this.getEscalas({
        funcionario: funcionarioId,
        data_inicio: dataInicio,
        data_fim: dataFim,
      });

      return response.results;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new EscalasApiService();