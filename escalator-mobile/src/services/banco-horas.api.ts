import { AxiosResponse } from 'axios';
import { BancoHoras } from '../types';
import { baseApi, handleApiError } from './base.api';

class BancoHorasApiService {
  // Listar registros do banco de horas
  async getBancoHoras(params?: {
    funcionario?: string;
    data_inicio?: string;
    data_fim?: string;
    tipo?: 'credito' | 'debito';
    page?: number;
    page_size?: number;
  }): Promise<{ results: BancoHoras[]; count: number; next: string | null; previous: string | null }> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.funcionario) queryParams.append('funcionario', params.funcionario);
      if (params?.data_inicio) queryParams.append('data_inicio', params.data_inicio);
      if (params?.data_fim) queryParams.append('data_fim', params.data_fim);
      if (params?.tipo) queryParams.append('tipo', params.tipo);
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const response = await baseApi.get(`/banco-horas/?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter registro do banco de horas por ID
  async getBancoHora(id: string): Promise<BancoHoras> {
    try {
      const response: AxiosResponse<BancoHoras> = await baseApi.get(`/banco-horas/${id}/`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Criar registro no banco de horas
  async createBancoHoras(bancoHoras: Omit<BancoHoras, 'id' | 'created_at'>): Promise<BancoHoras> {
    try {
      const response: AxiosResponse<BancoHoras> = await baseApi.post('/banco-horas/', bancoHoras);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar registro do banco de horas
  async updateBancoHoras(id: string, bancoHoras: Partial<BancoHoras>): Promise<BancoHoras> {
    try {
      const response: AxiosResponse<BancoHoras> = await baseApi.patch(`/banco-horas/${id}/`, bancoHoras);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar registro do banco de horas
  async deleteBancoHoras(id: string): Promise<void> {
    try {
      await baseApi.delete(`/banco-horas/${id}/`);
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter saldo atual do funcionário
  async getSaldoFuncionario(funcionarioId: string): Promise<{ saldo_horas: number; saldo_minutos: number }> {
    try {
      const response = await baseApi.get(`/banco-horas/saldo/${funcionarioId}/`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter histórico do banco de horas do funcionário
  async getHistoricoFuncionario(
    funcionarioId: string,
    params?: {
      data_inicio?: string;
      data_fim?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<{ results: BancoHoras[]; count: number; next: string | null; previous: string | null }> {
    try {
      return await this.getBancoHoras({
        funcionario: funcionarioId,
        ...params
      });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Registrar horas extras
  async registrarHorasExtras(
    funcionarioId: string,
    horas: number,
    minutos: number,
    data: string,
    descricao?: string
  ): Promise<BancoHoras> {
    try {
      return await this.createBancoHoras({
        funcionario: funcionarioId,
        tipo: 'credito',
        horas,
        minutos,
        data,
        descricao: descricao || 'Horas extras registradas'
      });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Registrar compensação de horas
  async registrarCompensacao(
    funcionarioId: string,
    horas: number,
    minutos: number,
    data: string,
    descricao?: string
  ): Promise<BancoHoras> {
    try {
      return await this.createBancoHoras({
        funcionario: funcionarioId,
        tipo: 'debito',
        horas,
        minutos,
        data,
        descricao: descricao || 'Compensação de horas'
      });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter relatório mensal
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
      
      const response = await baseApi.get(`/banco-horas/relatorio/${funcionarioId}/`, {
        params: {
          data_inicio: dataInicio,
          data_fim: dataFim
        }
      });
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new BancoHorasApiService();