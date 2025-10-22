import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const PerfilScreen: React.FC = () => {
  const { user, signOut, loading } = useAuth();
  const [notificacoes, setNotificacoes] = useState(true);
  const [localizacao, setLocalizacao] = useState(true);

  const handleLogout = () => {
    Alert.alert(
      'Sair do App',
      'Tem certeza que deseja sair?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { 
          text: 'Sair', 
          style: 'destructive',
          onPress: signOut 
        },
      ]
    );
  };

  const handleSobre = () => {
    Alert.alert(
      'Sobre o App',
      'Escalator v1.0.0\n\nSistema de Gerenciamento de Escalas e Pontos\n\nDesenvolvido para facilitar o controle de jornada de trabalho.',
      [{ text: 'OK' }]
    );
  };

  const handleAjuda = () => {
    Alert.alert(
      'Ajuda',
      'Para suporte técnico ou dúvidas sobre o sistema, entre em contato com o departamento de RH da sua empresa.\n\nE-mail: rh@empresa.com\nTelefone: (11) 1234-5678',
      [{ text: 'OK' }]
    );
  };

  if (loading) {
    return <LoadingSpinner message="Carregando perfil..." />;
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header do Perfil */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <Text style={styles.avatarText}>
            {user?.first_name?.charAt(0) || user?.username?.charAt(0) || '👤'}
          </Text>
        </View>
        <Text style={styles.userName}>
          {user?.first_name && user?.last_name 
            ? `${user.first_name} ${user.last_name}`
            : user?.username || 'Usuário'
          }
        </Text>
        <Text style={styles.userEmail}>{user?.email || 'email@empresa.com'}</Text>
      </View>

      {/* Informações do Usuário */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Informações Pessoais</Text>
        
        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Nome de usuário:</Text>
            <Text style={styles.infoValue}>{user?.username}</Text>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>E-mail:</Text>
            <Text style={styles.infoValue}>{user?.email || 'Não informado'}</Text>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Status:</Text>
            <Text style={[styles.infoValue, styles.statusActive]}>
              {user?.is_active ? '✅ Ativo' : '❌ Inativo'}
            </Text>
          </View>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Tipo de usuário:</Text>
            <Text style={styles.infoValue}>
              {user?.is_staff ? 'Administrador' : 'Funcionário'}
            </Text>
          </View>
        </View>
      </View>

      {/* Configurações */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Configurações</Text>
        
        <View style={styles.configCard}>
          <View style={styles.configRow}>
            <View style={styles.configInfo}>
              <Text style={styles.configLabel}>Notificações</Text>
              <Text style={styles.configDesc}>
                Receber lembretes de ponto e avisos
              </Text>
            </View>
            <Switch
              value={notificacoes}
              onValueChange={setNotificacoes}
              trackColor={{ false: '#d1d5db', true: '#2563eb' }}
              thumbColor={notificacoes ? '#ffffff' : '#f4f3f4'}
            />
          </View>
          
          <View style={styles.configRow}>
            <View style={styles.configInfo}>
              <Text style={styles.configLabel}>Localização</Text>
              <Text style={styles.configDesc}>
                Permitir registro de localização nos pontos
              </Text>
            </View>
            <Switch
              value={localizacao}
              onValueChange={setLocalizacao}
              trackColor={{ false: '#d1d5db', true: '#2563eb' }}
              thumbColor={localizacao ? '#ffffff' : '#f4f3f4'}
            />
          </View>
        </View>
      </View>

      {/* Menu de Ações */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Suporte</Text>
        
        <TouchableOpacity style={styles.menuItem} onPress={handleAjuda}>
          <Text style={styles.menuIcon}>❓</Text>
          <View style={styles.menuContent}>
            <Text style={styles.menuLabel}>Ajuda</Text>
            <Text style={styles.menuDesc}>Suporte e contato</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.menuItem} onPress={handleSobre}>
          <Text style={styles.menuIcon}>ℹ️</Text>
          <View style={styles.menuContent}>
            <Text style={styles.menuLabel}>Sobre o App</Text>
            <Text style={styles.menuDesc}>Versão e informações</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Botão de Logout */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutIcon}>🚪</Text>
          <Text style={styles.logoutText}>Sair do App</Text>
        </TouchableOpacity>
      </View>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Escalator v1.0.0
        </Text>
        <Text style={styles.footerText}>
          © 2024 Sistema de Escalas
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
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 32,
    color: 'white',
    fontWeight: 'bold',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 16,
    color: '#bfdbfe',
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
  infoCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  infoLabel: {
    fontSize: 16,
    color: '#6b7280',
    flex: 1,
  },
  infoValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    flex: 1,
    textAlign: 'right',
  },
  statusActive: {
    color: '#059669',
  },
  configCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  configRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  configInfo: {
    flex: 1,
  },
  configLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  configDesc: {
    fontSize: 14,
    color: '#6b7280',
  },
  menuItem: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  menuIcon: {
    fontSize: 24,
    marginRight: 16,
  },
  menuContent: {
    flex: 1,
  },
  menuLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  menuDesc: {
    fontSize: 14,
    color: '#6b7280',
  },
  menuArrow: {
    fontSize: 24,
    color: '#9ca3af',
  },
  logoutButton: {
    backgroundColor: '#dc2626',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#dc2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  logoutIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  logoutText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  footer: {
    alignItems: 'center',
    padding: 24,
  },
  footerText: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 4,
  },
});

export default PerfilScreen;