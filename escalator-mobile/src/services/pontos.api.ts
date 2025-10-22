import { AxiosResponse } from 'axios';
import { Ponto } from '../types';
import { baseApi, handleApiError } from './base.api';

class PontosApiService {
  // Registrar ponto
  async registrarPonto(
    funcionarioId: string,
    tipoRegistro: 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim',
    localizacao?: { latitude: number; longitude: number },
    observacoes?: string
  ): Promise<Ponto> {
    try {
      const response: AxiosResponse<Ponto> = await baseApi.post('/pontos/', {
        funcionario: funcionarioId,
        tipo_registro: tipoRegistro,
        timestamp: new Date().toISOString(),
        localizacao_lat: localizacao?.latitude,
        localizacao_lng: localizacao?.longitude,
        observacoes,
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Listar pontos
  async getPontos(params?: {
    funcionario?: string;
    data_inicio?: string;
    data_fim?: string;
    tipo_registro?: string;
    validado?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{ results: Ponto[]; count: number; next: string | null; previous: string | null }> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.funcionario) queryParams.append('funcionario', params.funcionario);
      if (params?.data_inicio) queryParams.append('data_inicio', params.data_inicio);
      if (params?.data_fim) queryParams.append('data_fim', params.data_fim);
      if (params?.tipo_registro) queryParams.append('tipo_registro', params.tipo_registro);
      if (params?.validado !== undefined) queryParams.append('validado', params.validado.toString());
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const response = await baseApi.get(`/pontos/?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter ponto por ID
  async getPonto(id: string): Promise<Ponto> {
    try {
      const response: AxiosResponse<Ponto> = await baseApi.get(`/pontos/${id}/`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter pontos de hoje
  async getPontosHoje(funcionarioId: string): Promise<Ponto[]> {
    try {
      const hoje = new Date().toISOString().split('T')[0];
      const response = await this.getPontos({
        funcionario: funcionarioId,
        data_inicio: hoje,
        data_fim: hoje
      });
      return response.results;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar ponto
  async updatePonto(id: string, ponto: Partial<Ponto>): Promise<Ponto> {
    try {
      const response: AxiosResponse<Ponto> = await baseApi.patch(`/pontos/${id}/`, ponto);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Validar ponto
  async validarPonto(id: string, validado: boolean = true): Promise<Ponto> {
    try {
      const response: AxiosResponse<Ponto> = await baseApi.patch(`/pontos/${id}/`, { validado });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar ponto
  async deletePonto(id: string): Promise<void> {
    try {
      await baseApi.delete(`/pontos/${id}/`);
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter último ponto do funcionário
  async getUltimoPonto(funcionarioId: string): Promise<Ponto | null> {
    try {
      const response = await this.getPontos({
        funcionario: funcionarioId,
        page_size: 1
      });
      return response.results.length > 0 ? response.results[0] : null;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter pontos da semana
  async getPontosSemana(funcionarioId: string, dataInicio: string): Promise<Ponto[]> {
    try {
      const dataFim = new Date(dataInicio);
      dataFim.setDate(dataFim.getDate() + 6);
      
      const response = await this.getPontos({
        funcionario: funcionarioId,
        data_inicio: dataInicio,
        data_fim: dataFim.toISOString().split('T')[0]
      });
      
      return response.results;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new PontosApiService();