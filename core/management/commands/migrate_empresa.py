"""
Comando para migrar dados existentes para o sistema multiempresa
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.core.management import call_command
from core.models import Empresa, Licenca
from core.routers import create_empresa_database, get_empresa_database
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Migra dados existentes para o sistema multiempresa'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-nome',
            type=str,
            required=True,
            help='Nome da empresa para migração',
        )
        parser.add_argument(
            '--empresa-cnpj',
            type=str,
            required=True,
            help='CNPJ da empresa (formato: XX.XXX.XXX/XXXX-XX)',
        )
        parser.add_argument(
            '--from-database',
            type=str,
            default='default',
            help='Banco de origem dos dados (padrão: default)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações (apenas mostra o que seria feito)',
        )
    
    def handle(self, *args, **options):
        empresa_nome = options['empresa_nome']
        empresa_cnpj = options['empresa_cnpj']
        from_database = options['from_database']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita')
            )
        
        try:
            # Cria empresa no banco master
            empresa = self.create_empresa_master(empresa_nome, empresa_cnpj, dry_run)
            
            if not dry_run and empresa:
                # Cria banco da empresa
                db_alias = create_empresa_database(empresa.id)
                
                # Migra dados do banco origem para o banco da empresa
                self.migrate_data(from_database, db_alias, empresa.id)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Migração concluída para empresa {empresa_nome}!')
                )
            
        except Exception as e:
            raise CommandError(f'Erro durante migração: {e}')
    
    def create_empresa_master(self, nome, cnpj, dry_run=False):
        """Cria empresa no banco master"""
        if dry_run:
            self.stdout.write(f'[DRY-RUN] Criaria empresa: {nome} - {cnpj}')
            return None
        
        try:
            with transaction.atomic(using='master'):
                # Verifica se empresa já existe
                if Empresa.objects.using('master').filter(cnpj=cnpj).exists():
                    raise CommandError(f'Empresa com CNPJ {cnpj} já existe no sistema')
                
                # Cria empresa
                empresa = Empresa.objects.using('master').create(
                    nome=nome,
                    razao_social=nome,
                    cnpj=cnpj,
                    email=f'contato@{nome.lower().replace(" ", "")}.com',
                    ativa=True
                )
                
                # Cria licença padrão
                Licenca.objects.using('master').create(
                    empresa=empresa,
                    tipo='basico',
                    status='ativa',
                    max_funcionarios=10,
                    max_usuarios=3,
                    permite_banco_horas=True,
                    permite_ponto_eletronico=True,
                    permite_relatorios_avancados=False,
                    permite_integracao_api=False,
                    data_inicio=datetime.now().date(),
                    data_fim=datetime.now().date() + timedelta(days=30),  # Trial de 30 dias
                    valor_mensal=99.90
                )
                
                self.stdout.write(f'Empresa criada: {empresa.nome} (ID: {empresa.id})')
                return empresa
                
        except Exception as e:
            raise CommandError(f'Erro ao criar empresa: {e}')
    
    def migrate_data(self, from_db, to_db, empresa_id):
        """Migra dados entre bancos"""
        self.stdout.write(f'Migrando dados de {from_db} para {to_db}...')
        
        # Lista de tabelas para migrar (excluindo tabelas do core)
        tables_to_migrate = [
            'escalator_funcionario',
            'escalator_turno',
            'escalator_escala',
            'escalator_folga',
            'escalator_escalapredefinida',
            'escalator_contrato',
            'escalator_ponto',
            'escalator_bancohoras',
            'escalator_configuracaosistema',
            'usuarios_usuario',
            'usuarios_perfil',
            'usuarios_grupo',
            'usuarios_permissao',
        ]
        
        from_conn = connections[from_db]
        to_conn = connections[to_db]
        
        try:
            with transaction.atomic(using=to_db):
                for table in tables_to_migrate:
                    self.migrate_table(from_conn, to_conn, table, empresa_id)
            
            self.stdout.write(
                self.style.SUCCESS('Dados migrados com sucesso!')
            )
            
        except Exception as e:
            raise CommandError(f'Erro ao migrar dados: {e}')
    
    def migrate_table(self, from_conn, to_conn, table_name, empresa_id):
        """Migra uma tabela específica"""
        try:
            with from_conn.cursor() as from_cursor:
                # Verifica se a tabela existe no banco origem
                from_cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """)
                
                if not from_cursor.fetchone():
                    self.stdout.write(f'Tabela {table_name} não encontrada no banco origem')
                    return
                
                # Busca dados da tabela
                from_cursor.execute(f"SELECT * FROM {table_name}")
                rows = from_cursor.fetchall()
                
                if not rows:
                    self.stdout.write(f'Tabela {table_name} está vazia')
                    return
                
                # Busca estrutura da tabela
                from_cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = from_cursor.fetchall()
                columns = [col[1] for col in columns_info]
                
            # Insere dados no banco destino
            with to_conn.cursor() as to_cursor:
                placeholders = ', '.join(['?' for _ in columns])
                columns_str = ', '.join(columns)
                
                # Adiciona empresa_id se a tabela tiver esse campo
                if 'empresa_id' in columns:
                    # Atualiza dados para incluir empresa_id
                    updated_rows = []
                    empresa_id_index = columns.index('empresa_id')
                    
                    for row in rows:
                        row_list = list(row)
                        row_list[empresa_id_index] = empresa_id
                        updated_rows.append(tuple(row_list))
                    
                    rows = updated_rows
                
                # Insere dados
                to_cursor.executemany(
                    f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    rows
                )
                
                self.stdout.write(f'Migrados {len(rows)} registros da tabela {table_name}')
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Erro ao migrar tabela {table_name}: {e}')
            )