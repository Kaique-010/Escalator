import { Funcionario } from '../types';
import { handleApiError } from './base.api';
import { apiGet, apiPost, apiPatch, apiDelete } from '../api/typedClient';

class FuncionariosApiService {
  // Obter funcionário por ID (tipado via OpenAPI)
  async getFuncionario(id: string): Promise<Funcionario> {
    try {
      const data = await apiGet('/api/funcionarios/{id}/', { path: { id: Number(id) } });
      return data as Funcionario;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Listar funcionários (tipado via OpenAPI)
  async getFuncionarios(params?: {
    search?: string;
    ativo?: boolean;
    cargo?: string;
    page?: number;
  }): Promise<{ results: Funcionario[]; count: number; next: string | null; previous: string | null }> {
    try {
      const data = await apiGet('/api/funcionarios/', {
        query: {
          search: params?.search,
          ativo: params?.ativo,
          ordering: undefined,
          page: params?.page,
        } as any,
      });
      return data as any;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Criar funcionário
  async createFuncionario(funcionario: Omit<Funcionario, 'id' | 'created_at'>): Promise<Funcionario> {
    try {
      const data = await apiPost('/api/funcionarios/', funcionario as any);
      return data as Funcionario;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar funcionário (PATCH)
  async updateFuncionario(id: string, funcionario: Partial<Funcionario>): Promise<Funcionario> {
    try {
      const data = await apiPatch('/api/funcionarios/{id}/', funcionario as any, { path: { id: Number(id) } });
      return data as Funcionario;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar funcionário
  async deleteFuncionario(id: string): Promise<void> {
    try {
      await apiDelete('/api/funcionarios/{id}/', { path: { id: Number(id) } });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Ativar/Desativar funcionário
  async toggleFuncionarioStatus(id: string, ativo: boolean): Promise<Funcionario> {
    try {
      const data = await apiPatch('/api/funcionarios/{id}/', { ativo } as any, { path: { id: Number(id) } });
      return data as Funcionario;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

export default new FuncionariosApiService();