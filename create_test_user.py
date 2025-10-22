#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from usuarios.models import Usuario, Perfil
from escalator.models import Funcionario
from django.contrib.auth.hashers import make_password

def create_test_user():
    """Cria um usuário de teste com funcionário associado"""
    
    try:
        # Dados do usuário de teste
        username = 'teste'
        email = 'teste@escalator.com'
        password = '123456'
        first_name = 'Usuário'
        last_name = 'Teste'
        
        # Verificar se o usuário já existe
        if Usuario.objects.filter(username=username).exists():
            print(f"Usuário '{username}' já existe. Removendo para recriar...")
            Usuario.objects.filter(username=username).delete()
        
        # Criar o usuário
        print(f"Criando usuário: {username}")
        usuario = Usuario.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
        
        # Criar perfil do usuário
        print("Criando perfil do usuário...")
        perfil = Perfil.objects.create(
            usuario=usuario,
            telefone='(11) 99999-9999',
            endereco='Rua Teste, 123',
            cidade='São Paulo',
            pais='Brasil',
            data_nascimento=date(1990, 1, 1),
            genero='M'
        )
        
        # Criar funcionário associado
        print("Criando funcionário associado...")
        funcionario = Funcionario.objects.create(
            usuario=usuario,
            nome=f"{first_name} {last_name}",
            matricula='TEST001',
            cargo='Desenvolvedor',
            ativo=True
        )
        
        print("\n" + "="*50)
        print("USUÁRIO DE TESTE CRIADO COM SUCESSO!")
        print("="*50)
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Funcionário ID: {funcionario.id}")
        print(f"Matrícula: {funcionario.matricula}")
        print("="*50)
        print("\nVocê pode usar essas credenciais para fazer login no app!")
        
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_test_user()