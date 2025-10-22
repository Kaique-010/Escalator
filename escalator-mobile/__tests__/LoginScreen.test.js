import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import LoginScreen from '../src/screens/LoginScreen';
import { AuthProvider } from '../src/contexts/AuthContext';
import ApiService from '../src/services/api';

// Mock do ApiService
jest.mock('../src/services/api', () => ({
  login: jest.fn(),
  getCurrentUser: jest.fn().mockResolvedValue(null),
  isAuthenticated: jest.fn().mockResolvedValue(false),
}));

// Mock do Alert
jest.spyOn(Alert, 'alert');

// Mock do AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  multiRemove: jest.fn(),
}));

// Mock do LoadingSpinner
jest.mock('../src/components/LoadingSpinner', () => {
  return function MockLoadingSpinner() {
    const { Text } = require('react-native');
    return React.createElement(Text, { testID: 'loading-spinner' }, 'Loading...');
  };
});

// Wrapper com AuthProvider
const LoginScreenWithProvider = () => 
  React.createElement(AuthProvider, null, React.createElement(LoginScreen));

describe('LoginScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('deve renderizar corretamente', async () => {
    const { getByText, getByPlaceholderText } = render(React.createElement(LoginScreenWithProvider));
    
    await waitFor(() => {
      expect(getByText('Escalator')).toBeTruthy();
      expect(getByText('Escalas Inteligentes')).toBeTruthy();
      expect(getByPlaceholderText('Digite seu usuário')).toBeTruthy();
      expect(getByPlaceholderText('Digite sua senha')).toBeTruthy();
      expect(getByText('Entrar')).toBeTruthy();
    });
  });

  it('deve permitir digitar nos campos de input', async () => {
    const { getByPlaceholderText } = render(React.createElement(LoginScreenWithProvider));
    
    await waitFor(() => {
      const usernameInput = getByPlaceholderText('Digite seu usuário');
      const passwordInput = getByPlaceholderText('Digite sua senha');

      fireEvent.changeText(usernameInput, 'admin');
      fireEvent.changeText(passwordInput, 'admin123');

      expect(usernameInput.props.value).toBe('admin');
      expect(passwordInput.props.value).toBe('admin123');
    });
  });

  it('deve mostrar erro quando campos estão vazios', async () => {
    const { getByText } = render(React.createElement(LoginScreenWithProvider));
    
    await waitFor(() => {
      const loginButton = getByText('Entrar');
      fireEvent.press(loginButton);
    });

    expect(Alert.alert).toHaveBeenCalledWith('Erro', 'Por favor, preencha todos os campos');
  });

  it('deve fazer login com credenciais válidas', async () => {
    const mockUser = {
      id: 1,
      username: 'admin',
      first_name: 'Admin',
      last_name: 'User',
      email: 'admin@test.com',
      is_active: true,
      is_staff: true,
    };

    ApiService.login.mockResolvedValue({
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      user: mockUser,
    });

    const { getByPlaceholderText, getByText } = render(React.createElement(LoginScreenWithProvider));
    
    await waitFor(() => {
      const usernameInput = getByPlaceholderText('Digite seu usuário');
      const passwordInput = getByPlaceholderText('Digite sua senha');
      
      fireEvent.changeText(usernameInput, 'admin');
      fireEvent.changeText(passwordInput, 'admin123');
      
      const loginButton = getByText('Entrar');
      fireEvent.press(loginButton);
    });

    // Deve chamar a API de login
    expect(ApiService.login).toHaveBeenCalledWith('admin', 'admin123');
  });

  it('deve mostrar erro com credenciais inválidas', async () => {
    ApiService.login.mockRejectedValue(new Error('Credenciais inválidas'));

    const { getByPlaceholderText, getByText } = render(React.createElement(LoginScreenWithProvider));
    
    await waitFor(() => {
      const usernameInput = getByPlaceholderText('Digite seu usuário');
      const passwordInput = getByPlaceholderText('Digite sua senha');
      
      fireEvent.changeText(usernameInput, 'wrong');
      fireEvent.changeText(passwordInput, 'wrong');
      
      const loginButton = getByText('Entrar');
      fireEvent.press(loginButton);
    });

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith('Erro', 'Credenciais inválidas');
    });
  });
});