import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { DashboardData, Escala } from '../types';

const DashboardScreen: React.FC = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      if (!user?.funcionario?.id) {
        console.error('Usuário não encontrado');
        Alert.alert('Erro', 'Usuário não encontrado. Faça login novamente.');
        return;
      }
      
      const data = await ApiService.getDashboard();
      setDashboardData(data);
    } catch (error: any) {
      Alert.alert('Erro', 'Não foi possível carregar os dados do dashboard');
      console.error('Erro ao carregar dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };

  const formatTime = (timeString: string) => {
    return timeString.slice(0, 5); // HH:MM
  };

  if (loading) {
    return <LoadingSpinner message="Carregando dashboard..." />;
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.greeting}>Olá, {user?.first_name || user?.username}!</Text>
        <Text style={styles.date}>{new Date().toLocaleDateString('pt-BR', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })}</Text>
      </View>

      {/* Cards de Resumo */}
      <View style={styles.cardsContainer}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Banco de Horas</Text>
          <Text style={styles.cardValue}>
            {dashboardData?.banco_horas_saldo || '0:00'}h
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Pontos Hoje</Text>
          <Text style={styles.cardValue}>
            {dashboardData?.pontos_hoje?.length || 0}
          </Text>
        </View>
      </View>

      {/* Próximas Escalas */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Próximas Escalas</Text>
        {dashboardData?.proximas_escalas && dashboardData.proximas_escalas.length > 0 ? (
          dashboardData.proximas_escalas.map((escala: Escala) => (
            <View key={escala.id} style={styles.escalaCard}>
              <View style={styles.escalaHeader}>
                <Text style={styles.escalaDate}>
                  {formatDate(escala.data_inicio)}
                </Text>
                <Text style={styles.escalaStatus}>
                  {escala.confirmada ? '✅ Confirmada' : '⏳ Pendente'}
                </Text>
              </View>
              <Text style={styles.escalaTime}>
                {formatTime(escala.hora_inicio)} - {formatTime(escala.hora_fim)}
              </Text>
              {escala.observacoes && (
                <Text style={styles.escalaObs}>{escala.observacoes}</Text>
              )}
            </View>
          ))
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Nenhuma escala programada</Text>
          </View>
        )}
      </View>

      {/* Pontos de Hoje */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Pontos de Hoje</Text>
        {dashboardData?.pontos_hoje && dashboardData.pontos_hoje.length > 0 ? (
          dashboardData.pontos_hoje.map((ponto, index) => (
            <View key={index} style={styles.pontoCard}>
              <View style={styles.pontoInfo}>
                <Text style={styles.pontoTipo}>
                  {ponto.tipo === 'entrada' ? '🟢 Entrada' :
                   ponto.tipo === 'saida' ? '🔴 Saída' :
                   ponto.tipo === 'pausa_inicio' ? '🟡 Início Pausa' :
                   '🟡 Fim Pausa'}
                </Text>
                <Text style={styles.pontoHora}>
                  {new Date(ponto.data_hora).toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </Text>
              </View>
              {ponto.localizacao && (
                <Text style={styles.pontoLocal}>📍 Localização registrada</Text>
              )}
            </View>
          ))
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Nenhum ponto registrado hoje</Text>
          </View>
        )}
      </View>

      {/* Ações Rápidas */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Ações Rápidas</Text>
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionButtonText}>📝 Registrar Ponto</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionButtonText}>📊 Ver Relatórios</Text>
          </TouchableOpacity>
        </View>
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
    paddingTop: 60,
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  date: {
    fontSize: 16,
    color: '#bfdbfe',
    textTransform: 'capitalize',
  },
  cardsContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  card: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  cardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
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
  escalaCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  escalaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  escalaDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  escalaStatus: {
    fontSize: 14,
    color: '#059669',
  },
  escalaTime: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2563eb',
    marginBottom: 4,
  },
  escalaObs: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  pontoCard: {
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
  pontoInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  pontoTipo: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  pontoHora: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  pontoLocal: {
    fontSize: 12,
    color: '#6b7280',
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
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#2563eb',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default DashboardScreen;