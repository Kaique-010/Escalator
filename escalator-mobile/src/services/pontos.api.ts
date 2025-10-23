import { Ponto } from '../types';
import { handleApiError } from './base.api';
import { apiGet, apiPost, apiPatch, apiDelete } from '../api/typedClient';

class PontosApiService {
  // Registrar ponto (cliente tipado)
  async registrarPonto(
    funcionarioId: string,
    tipoRegistro: 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim',
    localizacao?: { latitude: number; longitude: number },
    observacoes?: string
  ): Promise<Ponto> {
    try {
      const data = await apiPost('/api/pontos/', {
        funcionario: Number(funcionarioId),
        tipo_registro: tipoRegistro as any,
        timestamp: new Date().toISOString(),
        localizacao_lat: localizacao?.latitude ?? null,
        localizacao_lng: localizacao?.longitude ?? null,
        observacoes,
      } as any);
      return data as Ponto;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Listar pontos (cliente tipado)
  async getPontos(params?: {
    funcionario?: string;
    data_inicio?: string; // suportado no backend
    data_fim?: string; // suportado no backend
    tipo_registro?: 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim';
    validado?: boolean;
    page?: number;
  }): Promise<{ results: Ponto[]; count: number; next: string | null; previous: string | null }> {
    try {
      const data = await apiGet('/api/pontos/', {
        query: {
          funcionario: params?.funcionario ? Number(params.funcionario) : undefined,
          tipo_registro: params?.tipo_registro as any,
          validado: params?.validado,
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

  // Obter ponto por ID
  async getPonto(id: string): Promise<Ponto> {
    try {
      const data = await apiGet('/api/pontos/{id}/', { path: { id: Number(id) } });
      return data as Ponto;
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
        data_fim: hoje,
      });
      return response.results;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Atualizar ponto (PATCH)
  async updatePonto(id: string, ponto: Partial<Ponto>): Promise<Ponto> {
    try {
      const data = await apiPatch('/api/pontos/{id}/', ponto as any, { path: { id: Number(id) } });
      return data as Ponto;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Validar ponto (PATCH)
  async validarPonto(id: string, validado: boolean = true): Promise<Ponto> {
    try {
      const data = await apiPatch('/api/pontos/{id}/', { validado } as any, { path: { id: Number(id) } });
      return data as Ponto;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Deletar ponto
  async deletePonto(id: string): Promise<void> {
    try {
      await apiDelete('/api/pontos/{id}/', { path: { id: Number(id) } });
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter último ponto do funcionário
  async getUltimoPonto(funcionarioId: string): Promise<Ponto | null> {
    try {
      const response = await this.getPontos({ funcionario: funcionarioId, page: 1 });
      return response.results.length > 0 ? response.results[0] : null;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  // Obter pontos da semana
  async getPontosSemana(funcionarioId: string, dataInicio: string): Promise<Ponto[]> {
    try {
      const dataFimDate = new Date(dataInicio);
      dataFimDate.setDate(dataFimDate.getDate() + 6);
      const dataFim = dataFimDate.toISOString().split('T')[0];

      const response = await this.getPontos({
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

export default new PontosApiService();