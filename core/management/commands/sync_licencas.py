"""
Comando para sincronizar dados de licenças entre o banco master e os bancos das empresas
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from core.models import Empresa, Licenca
from core.routers import get_empresa_database
import json

class Command(BaseCommand):
    help = 'Sincroniza dados de licenças entre banco master e bancos das empresas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa específica para sincronizar (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações (apenas mostra o que seria feito)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a sincronização mesmo se os dados estiverem atualizados',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        empresa_id = options['empresa_id']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita')
            )
        
        try:
            if empresa_id:
                # Sincroniza apenas uma empresa específica
                self.sync_empresa_licenca(empresa_id, dry_run, force)
            else:
                # Sincroniza todas as empresas ativas
                self.sync_all_empresas(dry_run, force)
                
        except Exception as e:
            raise CommandError(f'Erro durante sincronização: {e}')
    
    def sync_all_empresas(self, dry_run=False, force=False):
        """Sincroniza licenças de todas as empresas ativas"""
        empresas = Empresa.objects.using('master').filter(ativa=True)
        
        self.stdout.write(f'Sincronizando {empresas.count()} empresas...')
        
        for empresa in empresas:
            try:
                self.sync_empresa_licenca(empresa.id, dry_run, force)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erro ao sincronizar empresa {empresa.nome}: {e}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS('Sincronização de todas as empresas concluída!')
        )
    
    def sync_empresa_licenca(self, empresa_id, dry_run=False, force=False):
        """Sincroniza licença de uma empresa específica"""
        try:
            # Busca empresa no banco master
            empresa = Empresa.objects.using('master').get(id=empresa_id, ativa=True)
            
            # Busca licença ativa no banco master
            licenca_master = Licenca.objects.using('master').filter(
                empresa=empresa,
                status='ativa'
            ).first()
            
            if not licenca_master:
                self.stdout.write(
                    self.style.WARNING(f'Nenhuma licença ativa encontrada para {empresa.nome}')
                )
                return
            
            # Obtém alias do banco da empresa
            db_alias = get_empresa_database(empresa_id)
            
            # Verifica se o banco da empresa existe
            if db_alias not in connections.databases:
                self.stdout.write(
                    self.style.WARNING(f'Banco da empresa {empresa.nome} não encontrado')
                )
                return
            
            # Prepara dados da licença para sincronização
            licenca_data = {
                'empresa_id': empresa.id,
                'empresa_nome': empresa.nome,
                'empresa_cnpj': empresa.cnpj,
                'tipo': licenca_master.tipo,
                'status': licenca_master.status,
                'max_funcionarios': licenca_master.max_funcionarios,
                'max_usuarios': licenca_master.max_usuarios,
                'permite_banco_horas': licenca_master.permite_banco_horas,
                'permite_ponto_eletronico': licenca_master.permite_ponto_eletronico,
                'permite_relatorios_avancados': licenca_master.permite_relatorios_avancados,
                'permite_integracao_api': licenca_master.permite_integracao_api,
                'data_inicio': licenca_master.data_inicio,
                'data_fim': licenca_master.data_fim,
                'valor_mensal': licenca_master.valor_mensal,
                'data_atualizacao': licenca_master.data_atualizacao,
            }
            
            if dry_run:
                self.stdout.write(f'[DRY-RUN] Sincronizaria licença para {empresa.nome}')
                self.stdout.write(f'Dados: {json.dumps(licenca_data, default=str, indent=2)}')
                return
            
            # Executa sincronização no banco da empresa
            self.create_or_update_licenca_copy(db_alias, licenca_data, force)
            
            self.stdout.write(
                self.style.SUCCESS(f'Licença sincronizada para {empresa.nome}')
            )
            
        except Empresa.DoesNotExist:
            raise CommandError(f'Empresa com ID {empresa_id} não encontrada ou inativa')
    
    def create_or_update_licenca_copy(self, db_alias, licenca_data, force=False):
        """Cria ou atualiza cópia da licença no banco da empresa"""
        from django.db import connection
        
        # Usa conexão direta para criar/atualizar tabela de licença
        with connections[db_alias].cursor() as cursor:
            # Cria tabela se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_licenca_copy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER NOT NULL,
                    empresa_nome VARCHAR(200) NOT NULL,
                    empresa_cnpj VARCHAR(18) NOT NULL,
                    tipo VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    max_funcionarios INTEGER,
                    max_usuarios INTEGER,
                    permite_banco_horas BOOLEAN NOT NULL,
                    permite_ponto_eletronico BOOLEAN NOT NULL,
                    permite_relatorios_avancados BOOLEAN NOT NULL,
                    permite_integracao_api BOOLEAN NOT NULL,
                    data_inicio DATE NOT NULL,
                    data_fim DATE,
                    valor_mensal DECIMAL(10, 2),
                    data_atualizacao DATETIME NOT NULL,
                    data_sincronizacao DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Verifica se já existe registro
            cursor.execute(
                "SELECT data_atualizacao FROM core_licenca_copy WHERE empresa_id = ?",
                [licenca_data['empresa_id']]
            )
            
            existing = cursor.fetchone()
            
            if existing and not force:
                # Compara datas de atualização
                existing_date = existing[0]
                new_date = licenca_data['data_atualizacao'].isoformat()
                
                if existing_date >= new_date:
                    return  # Dados já estão atualizados
            
            # Insere ou atualiza dados
            if existing:
                cursor.execute("""
                    UPDATE core_licenca_copy SET
                        empresa_nome = ?,
                        empresa_cnpj = ?,
                        tipo = ?,
                        status = ?,
                        max_funcionarios = ?,
                        max_usuarios = ?,
                        permite_banco_horas = ?,
                        permite_ponto_eletronico = ?,
                        permite_relatorios_avancados = ?,
                        permite_integracao_api = ?,
                        data_inicio = ?,
                        data_fim = ?,
                        valor_mensal = ?,
                        data_atualizacao = ?,
                        data_sincronizacao = CURRENT_TIMESTAMP
                    WHERE empresa_id = ?
                """, [
                    licenca_data['empresa_nome'],
                    licenca_data['empresa_cnpj'],
                    licenca_data['tipo'],
                    licenca_data['status'],
                    licenca_data['max_funcionarios'],
                    licenca_data['max_usuarios'],
                    licenca_data['permite_banco_horas'],
                    licenca_data['permite_ponto_eletronico'],
                    licenca_data['permite_relatorios_avancados'],
                    licenca_data['permite_integracao_api'],
                    licenca_data['data_inicio'],
                    licenca_data['data_fim'],
                    licenca_data['valor_mensal'],
                    licenca_data['data_atualizacao'],
                    licenca_data['empresa_id']
                ])
            else:
                cursor.execute("""
                    INSERT INTO core_licenca_copy (
                        empresa_id, empresa_nome, empresa_cnpj, tipo, status,
                        max_funcionarios, max_usuarios, permite_banco_horas,
                        permite_ponto_eletronico, permite_relatorios_avancados,
                        permite_integracao_api, data_inicio, data_fim,
                        valor_mensal, data_atualizacao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    licenca_data['empresa_id'],
                    licenca_data['empresa_nome'],
                    licenca_data['empresa_cnpj'],
                    licenca_data['tipo'],
                    licenca_data['status'],
                    licenca_data['max_funcionarios'],
                    licenca_data['max_usuarios'],
                    licenca_data['permite_banco_horas'],
                    licenca_data['permite_ponto_eletronico'],
                    licenca_data['permite_relatorios_avancados'],
                    licenca_data['permite_integracao_api'],
                    licenca_data['data_inicio'],
                    licenca_data['data_fim'],
                    licenca_data['valor_mensal'],
                    licenca_data['data_atualizacao']
                ])