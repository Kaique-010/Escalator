import { BancoHoras } from '../types';
import { handleApiError } from './base.api';
import { apiGet, apiPost, apiPatch, apiDelete } from '../api/typedClient';

class BancoHorasApiService {
  // Listar registros do banco de horas (cliente tipado)
  async getBancoHoras(params?: {
    funcionario?: string;
    data_inicio?: string; // suportado pelo backend
    data_fim?: string; // suportado pelo backend
    tipo?: 'credito' | 'debito';
    page?: number;
  }): Promise<{ results: BancoHoras[]; count: number; next: string | null; previous: string | null }> {
    try {
      const data = await apiGet('/api/banco-horas/', {
        query: {
          funcionario: params?.funcionario ? Number(params.funcionario) : undefined,
          tipo: params?.tipo as any,
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

  // Obter registro do banco de horas por ID (cliente tipado)
  async getBancoHora(id: string): Promise<BancoHoras> {
    try {
      const data = await apiGet('/api/banco-horas/{id}/', { path: { id: Number(id) } });
      return data as BancoHoras;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Criar registro no banco de horas (cliente tipado)
  async createBancoHoras(bancoHoras: Omit<BancoHoras, 'id' | 'created_at'>): Promise<BancoHoras> {
    try {
      const payload = {
        ...bancoHoras,
        funcionario: bancoHoras.funcionario ? Number(bancoHoras.funcionario as any) : undefined,
      } as any;
      const data = await apiPost('/api/banco-horas/', payload);
      return data as BancoHoras;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar registro do banco de horas (PATCH - cliente tipado)
  async updateBancoHoras(id: string, bancoHoras: Partial<BancoHoras>): Promise<BancoHoras> {
    try {
      const data = await apiPatch('/api/banco-horas/{id}/', bancoHoras as any, { path: { id: Number(id) } });
      return data as BancoHoras;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar registro do banco de horas (cliente tipado)
  async deleteBancoHoras(id: string): Promise<void> {
    try {
      await apiDelete('/api/banco-horas/{id}/', { path: { id: Number(id) } });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter saldo atual do funcionário (endpoint custom preservado)
  async getSaldoFuncionario(funcionarioId: string): Promise<{ saldo_horas: number; saldo_minutos: number }> {
    try {
      // Mantido endpoint custom fora do schema tipado
      const { baseApi } = await import('./base.api');
      const response = await baseApi.get(`/banco-horas/saldo/${funcionarioId}/`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter histórico do banco de horas do funcionário (usa listagem tipada)
  async getHistoricoFuncionario(
    funcionarioId: string,
    params?: {
      data_inicio?: string;
      data_fim?: string;
      page?: number;
    }
  ): Promise<{ results: BancoHoras[]; count: number; next: string | null; previous: string | null }> {
    try {
      return await this.getBancoHoras({ funcionario: funcionarioId, ...params });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Registrar horas extras (usa criação tipada)
  async registrarHorasExtras(
    funcionarioId: string,
    horas: number,
    minutos: number,
    data: string,
    descricao?: string
  ): Promise<BancoHoras> {
    try {
      return await this.createBancoHoras({
        funcionario: funcionarioId as any,
        tipo: 'credito',
        horas,
        minutos,
        data,
        descricao: descricao || 'Horas extras registradas',
      } as any);
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Registrar compensação de horas (usa criação tipada)
  async registrarCompensacao(
    funcionarioId: string,
    horas: number,
    minutos: number,
    data: string,
    descricao?: string
  ): Promise<BancoHoras> {
    try {
      return await this.createBancoHoras({
        funcionario: funcionarioId as any,
        tipo: 'debito',
        horas,
        minutos,
        data,
        descricao: descricao || 'Compensação de horas',
      } as any);
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter relatório mensal (endpoint custom preservado)
  async getRelatorioMensal(
    funcionarioId: string,
    ano: number,
    mes: number
  ): Promise<{
    creditos: BancoHoras[];
    debitos: BancoHoras[];
    saldo_inicial: number;
    saldo_final: number;
    total_creditos: number;
    total_debitos: number;
  }> {
    try {
      const dataInicio = new Date(ano, mes - 1, 1).toISOString().split('T')[0];
      const dataFim = new Date(ano, mes, 0).toISOString().split('T')[0];

      const { baseApi } = await import('./base.api');
      const response = await baseApi.get(`/banco-horas/relatorio/${funcionarioId}/`, {
        params: { data_inicio: dataInicio, data_fim: dataFim },
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new BancoHorasApiService();