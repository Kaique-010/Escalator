import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  RefreshControl,
} from 'react-native';
import * as Location from 'expo-location';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { Ponto } from '../types';

type TipoPonto = 'entrada' | 'saida' | 'pausa_inicio' | 'pausa_fim';

const PontosScreen: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [pontosHoje, setPontosHoje] = useState<Ponto[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);

  useEffect(() => {
    loadPontosHoje();
    requestLocationPermission();
  }, []);

  const requestLocationPermission = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const currentLocation = await Location.getCurrentPositionAsync({});
        setLocation(currentLocation);
      }
    } catch (error) {
      console.error('Erro ao obter localização:', error);
    }
  };

  const loadPontosHoje = async () => {
    try {
      const hoje = new Date().toISOString().split('T')[0];
      const pontos = await ApiService.getPontos({ data: hoje });
      setPontosHoje(pontos);
    } catch (error: any) {
      console.error('Erro ao carregar pontos:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPontosHoje();
    setRefreshing(false);
  };

  const registrarPonto = async (tipo: TipoPonto) => {
    try {
      setLoading(true);

      // Obter localização atual se disponível
      let currentLocation = location;
      if (!currentLocation) {
        try {
          currentLocation = await Location.getCurrentPositionAsync({});
          setLocation(currentLocation);
        } catch (error) {
          console.warn('Não foi possível obter a localização atual');
        }
      }

      const pontoData = {
        tipo,
        localizacao: currentLocation ? {
          latitude: currentLocation.coords.latitude,
          longitude: currentLocation.coords.longitude,
        } : undefined,
      };

      await ApiService.registrarPonto(pontoData);
      
      Alert.alert(
        'Sucesso',
        `Ponto de ${getTipoLabel(tipo)} registrado com sucesso!`,
        [{ text: 'OK', onPress: () => loadPontosHoje() }]
      );
    } catch (error: any) {
      Alert.alert('Erro', error.message || 'Não foi possível registrar o ponto');
    } finally {
      setLoading(false);
    }
  };

  const getTipoLabel = (tipo: TipoPonto): string => {
    const labels = {
      entrada: 'entrada',
      saida: 'saída',
      pausa_inicio: 'início da pausa',
      pausa_fim: 'fim da pausa',
    };
    return labels[tipo];
  };

  const getTipoIcon = (tipo: TipoPonto): string => {
    const icons = {
      entrada: '🟢',
      saida: '🔴',
      pausa_inicio: '🟡',
      pausa_fim: '🟡',
    };
    return icons[tipo];
  };

  const formatDateTime = (dateTimeString: string) => {
    const date = new Date(dateTimeString);
    return {
      time: date.toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      date: date.toLocaleDateString('pt-BR'),
    };
  };

  const getProximoTipoPonto = (): TipoPonto => {
    if (pontosHoje.length === 0) return 'entrada';
    
    const ultimoPonto = pontosHoje[pontosHoje.length - 1];
    
    switch (ultimoPonto.tipo) {
      case 'entrada':
        return 'pausa_inicio';
      case 'pausa_inicio':
        return 'pausa_fim';
      case 'pausa_fim':
        return 'saida';
      case 'saida':
        return 'entrada';
      default:
        return 'entrada';
    }
  };

  const proximoTipo = getProximoTipoPonto();

  if (loading && pontosHoje.length === 0) {
    return <LoadingSpinner message="Carregando pontos..." />;
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Status da Localização */}
      <View style={styles.locationStatus}>
        <Text style={styles.locationText}>
          {location ? '📍 Localização ativa' : '📍 Localização não disponível'}
        </Text>
        {!location && (
          <TouchableOpacity onPress={requestLocationPermission}>
            <Text style={styles.locationButton}>Ativar localização</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Botão de Registro */}
      <View style={styles.registroContainer}>
        <Text style={styles.registroTitle}>Registrar Ponto</Text>
        <TouchableOpacity
          style={[styles.registroButton, loading && styles.registroButtonDisabled]}
          onPress={() => registrarPonto(proximoTipo)}
          disabled={loading}
        >
          <Text style={styles.registroIcon}>
            {getTipoIcon(proximoTipo)}
          </Text>
          <Text style={styles.registroButtonText}>
            {loading ? 'Registrando...' : `Registrar ${getTipoLabel(proximoTipo)}`}
          </Text>
          <Text style={styles.registroTime}>
            {new Date().toLocaleTimeString('pt-BR', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Pontos de Hoje */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Pontos de Hoje</Text>
        {pontosHoje.length > 0 ? (
          pontosHoje.map((ponto, index) => {
            const { time, date } = formatDateTime(ponto.data_hora);
            return (
              <View key={index} style={styles.pontoCard}>
                <View style={styles.pontoHeader}>
                  <View style={styles.pontoInfo}>
                    <Text style={styles.pontoTipo}>
                      {getTipoIcon(ponto.tipo)} {getTipoLabel(ponto.tipo).toUpperCase()}
                    </Text>
                    <Text style={styles.pontoHora}>{time}</Text>
                  </View>
                  {ponto.localizacao && (
                    <Text style={styles.pontoLocal}>📍</Text>
                  )}
                </View>
                {ponto.observacoes && (
                  <Text style={styles.pontoObs}>{ponto.observacoes}</Text>
                )}
              </View>
            );
          })
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>⏰</Text>
            <Text style={styles.emptyText}>Nenhum ponto registrado hoje</Text>
            <Text style={styles.emptySubtext}>
              Registre seu primeiro ponto do dia
            </Text>
          </View>
        )}
      </View>

      {/* Botões de Ação Manual */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Registros Manuais</Text>
        <View style={styles.manualButtonsContainer}>
          <TouchableOpacity
            style={[styles.manualButton, styles.entradaButton]}
            onPress={() => registrarPonto('entrada')}
            disabled={loading}
          >
            <Text style={styles.manualButtonText}>🟢 Entrada</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.manualButton, styles.pausaButton]}
            onPress={() => registrarPonto('pausa_inicio')}
            disabled={loading}
          >
            <Text style={styles.manualButtonText}>🟡 Pausa</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.manualButton, styles.pausaButton]}
            onPress={() => registrarPonto('pausa_fim')}
            disabled={loading}
          >
            <Text style={styles.manualButtonText}>🟡 Volta</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.manualButton, styles.saidaButton]}
            onPress={() => registrarPonto('saida')}
            disabled={loading}
          >
            <Text style={styles.manualButtonText}>🔴 Saída</Text>
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
  locationStatus: {
    backgroundColor: 'white',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  locationText: {
    fontSize: 16,
    color: '#374151',
  },
  locationButton: {
    fontSize: 14,
    color: '#2563eb',
    fontWeight: '600',
  },
  registroContainer: {
    margin: 16,
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
  registroTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 20,
  },
  registroButton: {
    backgroundColor: '#2563eb',
    borderRadius: 20,
    paddingVertical: 20,
    paddingHorizontal: 32,
    alignItems: 'center',
    minWidth: 200,
    shadowColor: '#2563eb',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  registroButtonDisabled: {
    backgroundColor: '#9ca3af',
    shadowOpacity: 0.1,
  },
  registroIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  registroButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
    textTransform: 'capitalize',
  },
  registroTime: {
    color: '#bfdbfe',
    fontSize: 16,
    fontWeight: '600',
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
  pontoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pontoInfo: {
    flex: 1,
  },
  pontoTipo: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  pontoHora: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  pontoLocal: {
    fontSize: 20,
    color: '#059669',
  },
  pontoObs: {
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
  manualButtonsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  manualButton: {
    flex: 1,
    minWidth: '45%',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  entradaButton: {
    backgroundColor: '#059669',
  },
  pausaButton: {
    backgroundColor: '#d97706',
  },
  saidaButton: {
    backgroundColor: '#dc2626',
  },
  manualButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default PontosScreen;