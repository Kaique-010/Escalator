"""
Comando para configurar o sistema multiempresa
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.core.management import call_command
from core.models import Empresa, Licenca
from core.routers import create_empresa_database
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Configura o sistema multiempresa criando bancos e estruturas necessárias'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-master',
            action='store_true',
            help='Cria e migra o banco master',
        )
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa para criar banco específico',
        )
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='Cria dados de exemplo',
        )
    
    def handle(self, *args, **options):
        if options['create_master']:
            self.create_master_database()
        
        if options['empresa_id']:
            self.create_empresa_database(options['empresa_id'])
        
        if options['create_sample']:
            self.create_sample_data()
        
        if not any([options['create_master'], options['empresa_id'], options['create_sample']]):
            self.stdout.write(
                self.style.WARNING('Nenhuma ação especificada. Use --help para ver as opções.')
            )
    
    def create_master_database(self):
        """Cria e migra o banco master"""
        self.stdout.write('Criando banco master...')
        
        try:
            # Executa migrações no banco master
            call_command('migrate', '--database=master', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('Banco master criado e migrado com sucesso!')
            )
        except Exception as e:
            raise CommandError(f'Erro ao criar banco master: {e}')
    
    def create_empresa_database(self, empresa_id):
        """Cria banco específico para uma empresa"""
        self.stdout.write(f'Criando banco para empresa {empresa_id}...')
        
        try:
            # Verifica se a empresa existe no banco master
            empresa = Empresa.objects.using('master').get(id=empresa_id)
            
            # Cria o banco da empresa
            db_alias = create_empresa_database(empresa_id)
            
            # Executa migrações no banco da empresa (exceto core e algumas específicas)
            try:
                call_command('migrate', f'--database={db_alias}', 'contenttypes', verbosity=0)
                call_command('migrate', f'--database={db_alias}', 'auth', verbosity=0)
                call_command('migrate', f'--database={db_alias}', 'admin', verbosity=0)
                call_command('migrate', f'--database={db_alias}', 'sessions', verbosity=0)
                call_command('migrate', f'--database={db_alias}', 'usuarios', verbosity=0)
                
                # Para escalator, executa apenas as migrações básicas, pulando as que podem causar problemas
                call_command('migrate', f'--database={db_alias}', 'escalator', '0002_escalapredefinida', verbosity=0)
                
            except Exception as migration_error:
                self.stdout.write(
                    self.style.WARNING(f'Aviso: Algumas migrações podem ter falhado: {migration_error}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Banco da empresa {empresa.nome} criado com sucesso!')
            )
            
        except Empresa.DoesNotExist:
            raise CommandError(f'Empresa com ID {empresa_id} não encontrada no banco master')
        except Exception as e:
            raise CommandError(f'Erro ao criar banco da empresa: {e}')
    
    def create_sample_data(self):
        """Cria dados de exemplo"""
        self.stdout.write('Criando dados de exemplo...')
        
        try:
            with transaction.atomic(using='master'):
                # Cria empresa de exemplo
                empresa, created = Empresa.objects.using('master').get_or_create(
                    cnpj='12.345.678/0001-90',
                    defaults={
                        'nome': 'Empresa Exemplo Ltda',
                        'razao_social': 'Empresa Exemplo Ltda',
                        'email': 'contato@exemplo.com',
                        'telefone': '(11) 1234-5678',
                        'endereco': 'Rua Exemplo, 123',
                        'cidade': 'São Paulo',
                        'estado': 'SP',
                        'cep': '01234-567',
                        'ativa': True,
                    }
                )
                
                if created:
                    self.stdout.write(f'Empresa criada: {empresa.nome}')
                else:
                    self.stdout.write(f'Empresa já existe: {empresa.nome}')
                
                # Cria licença para a empresa
                licenca, created = Licenca.objects.using('master').get_or_create(
                    empresa=empresa,
                    defaults={
                        'tipo': 'profissional',
                        'status': 'ativa',
                        'max_funcionarios': 50,
                        'max_usuarios': 10,
                        'permite_banco_horas': True,
                        'permite_ponto_eletronico': True,
                        'permite_relatorios_avancados': True,
                        'permite_integracao_api': False,
                        'data_inicio': datetime.now().date(),
                        'data_fim': (datetime.now() + timedelta(days=365)).date(),
                        'valor_mensal': 299.90,
                    }
                )
                
                if created:
                    self.stdout.write(f'Licença criada para {empresa.nome}')
                else:
                    self.stdout.write(f'Licença já existe para {empresa.nome}')
                
                # Cria banco da empresa
                self.create_empresa_database(empresa.id)
                
            self.stdout.write(
                self.style.SUCCESS('Dados de exemplo criados com sucesso!')
            )
            
        except Exception as e:
            raise CommandError(f'Erro ao criar dados de exemplo: {e}')