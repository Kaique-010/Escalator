import AsyncStorage from '@react-native-async-storage/async-storage';

export class StorageService {
  // Chaves para armazenamento
  private static readonly KEYS = {
    AUTH_TOKEN: '@escalator:auth_token',
    REFRESH_TOKEN: '@escalator:refresh_token',
    USER_DATA: '@escalator:user_data',
    OFFLINE_PONTOS: '@escalator:offline_pontos',
    SETTINGS: '@escalator:settings',
    LAST_SYNC: '@escalator:last_sync',
  } as const;

  // Métodos para autenticação
  static async setAuthToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.AUTH_TOKEN, token);
    } catch (error) {
      console.error('Erro ao salvar token de autenticação:', error);
    }
  }

  static async getAuthToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(this.KEYS.AUTH_TOKEN);
    } catch (error) {
      console.error('Erro ao obter token de autenticação:', error);
      return null;
    }
  }

  static async setRefreshToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.REFRESH_TOKEN, token);
    } catch (error) {
      console.error('Erro ao salvar refresh token:', error);
    }
  }

  static async getRefreshToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(this.KEYS.REFRESH_TOKEN);
    } catch (error) {
      console.error('Erro ao obter refresh token:', error);
      return null;
    }
  }

  // Métodos para dados do usuário
  static async setUserData(userData: any): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.USER_DATA, JSON.stringify(userData));
    } catch (error) {
      console.error('Erro ao salvar dados do usuário:', error);
    }
  }

  static async getUserData(): Promise<any | null> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.USER_DATA);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Erro ao obter dados do usuário:', error);
      return null;
    }
  }

  // Métodos para pontos offline
  static async addOfflinePoint(ponto: any): Promise<void> {
    try {
      const existingPoints = await this.getOfflinePoints();
      const updatedPoints = [...existingPoints, { ...ponto, id: Date.now().toString() }];
      await AsyncStorage.setItem(this.KEYS.OFFLINE_PONTOS, JSON.stringify(updatedPoints));
    } catch (error) {
      console.error('Erro ao salvar ponto offline:', error);
    }
  }

  static async getOfflinePoints(): Promise<any[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.OFFLINE_PONTOS);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Erro ao obter pontos offline:', error);
      return [];
    }
  }

  static async clearOfflinePoints(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.KEYS.OFFLINE_PONTOS);
    } catch (error) {
      console.error('Erro ao limpar pontos offline:', error);
    }
  }

  static async removeOfflinePoint(pointId: string): Promise<void> {
    try {
      const existingPoints = await this.getOfflinePoints();
      const updatedPoints = existingPoints.filter(point => point.id !== pointId);
      await AsyncStorage.setItem(this.KEYS.OFFLINE_PONTOS, JSON.stringify(updatedPoints));
    } catch (error) {
      console.error('Erro ao remover ponto offline:', error);
    }
  }

  // Métodos para configurações
  static async setSettings(settings: any): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.SETTINGS, JSON.stringify(settings));
    } catch (error) {
      console.error('Erro ao salvar configurações:', error);
    }
  }

  static async getSettings(): Promise<any> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.SETTINGS);
      return data ? JSON.parse(data) : {
        notifications: true,
        location: true,
        autoSync: true,
        theme: 'light',
      };
    } catch (error) {
      console.error('Erro ao obter configurações:', error);
      return {
        notifications: true,
        location: true,
        autoSync: true,
        theme: 'light',
      };
    }
  }

  // Métodos para sincronização
  static async setLastSync(timestamp: number): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.LAST_SYNC, timestamp.toString());
    } catch (error) {
      console.error('Erro ao salvar timestamp de sincronização:', error);
    }
  }

  static async getLastSync(): Promise<number | null> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.LAST_SYNC);
      return data ? parseInt(data, 10) : null;
    } catch (error) {
      console.error('Erro ao obter timestamp de sincronização:', error);
      return null;
    }
  }

  // Métodos utilitários
  static async clearAllData(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        this.KEYS.AUTH_TOKEN,
        this.KEYS.REFRESH_TOKEN,
        this.KEYS.USER_DATA,
        this.KEYS.OFFLINE_PONTOS,
        this.KEYS.LAST_SYNC,
      ]);
    } catch (error) {
      console.error('Erro ao limpar todos os dados:', error);
    }
  }

  static async getAllKeys(): Promise<string[]> {
    try {
      return await AsyncStorage.getAllKeys();
    } catch (error) {
      console.error('Erro ao obter todas as chaves:', error);
      return [];
    }
  }

  static async getStorageSize(): Promise<number> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      let totalSize = 0;
      
      for (const key of keys) {
        if (key.startsWith('@escalator:')) {
          const value = await AsyncStorage.getItem(key);
          if (value) {
            totalSize += new Blob([value]).size;
          }
        }
      }
      
      return totalSize;
    } catch (error) {
      console.error('Erro ao calcular tamanho do storage:', error);
      return 0;
    }
  }
}