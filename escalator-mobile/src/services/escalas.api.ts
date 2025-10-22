import { AxiosResponse } from 'axios';
import { Escala } from '../types';
import { baseApi, handleApiError } from './base.api';

class EscalasApiService {
  // Listar escalas
  async getEscalas(params?: {
    funcionario?: string;
    data_inicio?: string;
    data_fim?: string;
    tipo_escala?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ results: Escala[]; count: number; next: string | null; previous: string | null }> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.funcionario) queryParams.append('funcionario', params.funcionario);
      if (params?.data_inicio) queryParams.append('data_inicio', params.data_inicio);
      if (params?.data_fim) queryParams.append('data_fim', params.data_fim);
      if (params?.tipo_escala) queryParams.append('tipo_escala', params.tipo_escala);
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const response = await baseApi.get(`/escalas/?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter escala por ID
  async getEscala(id: string): Promise<Escala> {
    try {
      const response: AxiosResponse<Escala> = await baseApi.get(`/escalas/${id}/`);
      return response.data;
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
        data_fim: hoje
      });
      return response.results.length > 0 ? response.results[0] : null;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Criar escala
  async createEscala(escala: Omit<Escala, 'id' | 'created_at'>): Promise<Escala> {
    try {
      const response: AxiosResponse<Escala> = await baseApi.post('/escalas/', escala);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar escala
  async updateEscala(id: string, escala: Partial<Escala>): Promise<Escala> {
    try {
      const response: AxiosResponse<Escala> = await baseApi.patch(`/escalas/${id}/`, escala);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar escala
  async deleteEscala(id: string): Promise<void> {
    try {
      await baseApi.delete(`/escalas/${id}/`);
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter escalas da semana
  async getEscalasSemana(funcionarioId: string, dataInicio: string): Promise<Escala[]> {
    try {
      const dataFim = new Date(dataInicio);
      dataFim.setDate(dataFim.getDate() + 6);
      
      const response = await this.getEscalas({
        funcionario: funcionarioId,
        data_inicio: dataInicio,
        data_fim: dataFim.toISOString().split('T')[0]
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
        data_fim: dataFim
      });
      
      return response.results;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new EscalasApiService();