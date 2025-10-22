import { AxiosResponse } from 'axios';
import { Funcionario } from '../types';
import { baseApi, handleApiError } from './base.api';

class FuncionariosApiService {
  // Obter funcionário por ID
  async getFuncionario(id: string): Promise<Funcionario> {
    try {
      const response: AxiosResponse<Funcionario> = await baseApi.get(`/funcionarios/${id}/`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Listar funcionários
  async getFuncionarios(params?: {
    search?: string;
    ativo?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{ results: Funcionario[]; count: number; next: string | null; previous: string | null }> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.search) queryParams.append('search', params.search);
      if (params?.ativo !== undefined) queryParams.append('ativo', params.ativo.toString());
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const response = await baseApi.get(`/funcionarios/?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Criar funcionário
  async createFuncionario(funcionario: Omit<Funcionario, 'id' | 'created_at'>): Promise<Funcionario> {
    try {
      const response: AxiosResponse<Funcionario> = await baseApi.post('/funcionarios/', funcionario);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar funcionário
  async updateFuncionario(id: string, funcionario: Partial<Funcionario>): Promise<Funcionario> {
    try {
      const response: AxiosResponse<Funcionario> = await baseApi.patch(`/funcionarios/${id}/`, funcionario);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar funcionário
  async deleteFuncionario(id: string): Promise<void> {
    try {
      await baseApi.delete(`/funcionarios/${id}/`);
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Ativar/Desativar funcionário
  async toggleFuncionarioStatus(id: string, ativo: boolean): Promise<Funcionario> {
    try {
      const response: AxiosResponse<Funcionario> = await baseApi.patch(`/funcionarios/${id}/`, { ativo });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new FuncionariosApiService();