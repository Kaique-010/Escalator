import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { BancoHoras } from '../types';

const BancoHorasScreen: React.FC = () => {
  const { user } = useAuth();
  const [bancoHoras, setBancoHoras] = useState<BancoHoras[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saldoTotal, setSaldoTotal] = useState('0:00');

  useEffect(() => {
    loadBancoHoras();
  }, []);

  const loadBancoHoras = async () => {
    try {
      const data = await ApiService.getBancoHoras();
      setBancoHoras(data);
      
      // Calcular saldo total
      const saldo = calcularSaldoTotal(data);
      setSaldoTotal(saldo);
    } catch (error: any) {
      console.error('Erro ao carregar banco de horas:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadBancoHoras();
    setRefreshing(false);
  };

  const calcularSaldoTotal = (registros: BancoHoras[]): string => {
    let totalMinutos = 0;
    
    registros.forEach(registro => {
      const [horas, minutos] = registro.saldo.split(':').map(Number);
      const minutosRegistro = horas * 60 + minutos;
      
      if (registro.tipo === 'credito') {
        totalMinutos += minutosRegistro;
      } else {
        totalMinutos -= minutosRegistro;
      }
    });

    const horasTotal = Math.floor(Math.abs(totalMinutos) / 60);
    const minutosRestantes = Math.abs(totalMinutos) % 60;
    const sinal = totalMinutos < 0 ? '-' : '';
    
    return `${sinal}${horasTotal.toString().padStart(2, '0')}:${minutosRestantes.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const getTipoIcon = (tipo: string) => {
    return tipo === 'credito' ? '➕' : '➖';
  };

  const getTipoColor = (tipo: string) => {
    return tipo === 'credito' ? '#059669' : '#dc2626';
  };

  const getSaldoColor = (saldo: string) => {
    return saldo.startsWith('-') ? '#dc2626' : '#059669';
  };

  if (loading) {
    return <LoadingSpinner message="Carregando banco de horas..." />;
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header com Saldo Total */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Saldo Total</Text>
        <Text style={[styles.saldoTotal, { color: getSaldoColor(saldoTotal) }]}>
          {saldoTotal}h
        </Text>
        <Text style={styles.headerSubtitle}>
          {saldoTotal.startsWith('-') ? 'Horas em débito' : 'Horas em crédito'}
        </Text>
      </View>

      {/* Resumo Mensal */}
      <View style={styles.resumoContainer}>
        <Text style={styles.sectionTitle}>Resumo do Mês</Text>
        <View style={styles.resumoCards}>
          <View style={styles.resumoCard}>
            <Text style={styles.resumoLabel}>Créditos</Text>
            <Text style={[styles.resumoValue, { color: '#059669' }]}>
              {bancoHoras
                .filter(b => b.tipo === 'credito')
                .reduce((acc, b) => {
                  const [h, m] = b.saldo.split(':').map(Number);
                  return acc + h * 60 + m;
                }, 0) / 60}h
            </Text>
          </View>
          
          <View style={styles.resumoCard}>
            <Text style={styles.resumoLabel}>Débitos</Text>
            <Text style={[styles.resumoValue, { color: '#dc2626' }]}>
              {bancoHoras
                .filter(b => b.tipo === 'debito')
                .reduce((acc, b) => {
                  const [h, m] = b.saldo.split(':').map(Number);
                  return acc + h * 60 + m;
                }, 0) / 60}h
            </Text>
          </View>
        </View>
      </View>

      {/* Histórico de Movimentações */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Histórico de Movimentações</Text>
        
        {bancoHoras.length > 0 ? (
          bancoHoras.map((registro) => (
            <View key={registro.id} style={styles.registroCard}>
              <View style={styles.registroHeader}>
                <View style={styles.registroInfo}>
                  <Text style={styles.registroData}>
                    {formatDate(registro.data)}
                  </Text>
                  <Text style={styles.registroDescricao}>
                    {registro.descricao}
                  </Text>
                </View>
                
                <View style={styles.registroSaldo}>
                  <Text style={styles.registroTipo}>
                    {getTipoIcon(registro.tipo)}
                  </Text>
                  <Text style={[
                    styles.registroHoras,
                    { color: getTipoColor(registro.tipo) }
                  ]}>
                    {registro.saldo}h
                  </Text>
                </View>
              </View>
              
              {registro.observacoes && (
                <Text style={styles.registroObs}>
                  {registro.observacoes}
                </Text>
              )}
            </View>
          ))
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📊</Text>
            <Text style={styles.emptyText}>Nenhum registro encontrado</Text>
            <Text style={styles.emptySubtext}>
              Suas movimentações de banco de horas aparecerão aqui
            </Text>
          </View>
        )}
      </View>

      {/* Informações Importantes */}
      <View style={styles.infoContainer}>
        <Text style={styles.infoTitle}>ℹ️ Informações Importantes</Text>
        <Text style={styles.infoText}>
          • O banco de horas é calculado automaticamente com base nos seus registros de ponto
        </Text>
        <Text style={styles.infoText}>
          • Horas extras são creditadas após 8h diárias ou 44h semanais
        </Text>
        <Text style={styles.infoText}>
          • O saldo pode ser utilizado para compensar faltas ou saídas antecipadas
        </Text>
        <Text style={styles.infoText}>
          • Consulte o RH para mais informações sobre políticas da empresa
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    backgroundColor: '#2563eb',
    padding: 24,
    paddingTop: 40,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    color: '#bfdbfe',
    marginBottom: 8,
  },
  saldoTotal: {
    fontSize: 48,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#bfdbfe',
  },
  resumoContainer: {
    margin: 16,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resumoCards: {
    flexDirection: 'row',
    gap: 12,
  },
  resumoCard: {
    flex: 1,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  resumoLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  resumoValue: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  section: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  registroCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  registroHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  registroInfo: {
    flex: 1,
  },
  registroData: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  registroDescricao: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  registroSaldo: {
    alignItems: 'center',
  },
  registroTipo: {
    fontSize: 20,
    marginBottom: 4,
  },
  registroHoras: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  registroObs: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
    marginTop: 8,
  },
  emptyState: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  infoContainer: {
    margin: 16,
    backgroundColor: '#fef3c7',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#92400e',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#92400e',
    marginBottom: 8,
    lineHeight: 20,
  },
});

export default BancoHorasScreen;