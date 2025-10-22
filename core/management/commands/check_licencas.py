"""
Comando para verificar status das licenças e limites das empresas
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from core.models import Empresa, Licenca
from core.routers import get_empresa_database
from datetime import datetime, timedelta
import json

class Command(BaseCommand):
    help = 'Verifica status das licenças e limites das empresas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa específica para verificar (opcional)',
        )
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Mostra apenas licenças expiradas ou próximas do vencimento',
        )
        parser.add_argument(
            '--json-output',
            action='store_true',
            help='Saída em formato JSON',
        )
        parser.add_argument(
            '--days-warning',
            type=int,
            default=7,
            help='Dias de antecedência para aviso de vencimento (padrão: 7)',
        )
    
    def handle(self, *args, **options):
        empresa_id = options['empresa_id']
        expired_only = options['expired_only']
        json_output = options['json_output']
        days_warning = options['days_warning']
        
        try:
            if empresa_id:
                # Verifica apenas uma empresa específica
                result = self.check_empresa_licenca(empresa_id, days_warning)
                results = [result] if result else []
            else:
                # Verifica todas as empresas
                results = self.check_all_empresas(days_warning)
            
            # Filtra apenas expiradas se solicitado
            if expired_only:
                results = [r for r in results if r['status'] in ['expirada', 'vencendo']]
            
            # Saída em JSON ou texto
            if json_output:
                self.stdout.write(json.dumps(results, default=str, indent=2))
            else:
                self.display_results(results)
                
        except Exception as e:
            raise CommandError(f'Erro durante verificação: {e}')
    
    def check_all_empresas(self, days_warning):
        """Verifica licenças de todas as empresas"""
        empresas = Empresa.objects.using('master').filter(ativa=True)
        results = []
        
        for empresa in empresas:
            try:
                result = self.check_empresa_licenca(empresa.id, days_warning)
                if result:
                    results.append(result)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erro ao verificar empresa {empresa.nome}: {e}')
                )
                continue
        
        return results
    
    def check_empresa_licenca(self, empresa_id, days_warning):
        """Verifica licença de uma empresa específica"""
        try:
            # Busca empresa no banco master
            empresa = Empresa.objects.using('master').get(id=empresa_id, ativa=True)
            
            # Busca licença ativa no banco master
            licenca = Licenca.objects.using('master').filter(
                empresa=empresa,
                status='ativa'
            ).first()
            
            if not licenca:
                return {
                    'empresa_id': empresa.id,
                    'empresa_nome': empresa.nome,
                    'status': 'sem_licenca',
                    'mensagem': 'Nenhuma licença ativa encontrada'
                }
            
            # Verifica status da licença
            hoje = datetime.now().date()
            status_licenca = 'ativa'
            mensagem = 'Licença ativa'
            
            if licenca.data_fim and licenca.data_fim < hoje:
                status_licenca = 'expirada'
                mensagem = f'Licença expirada em {licenca.data_fim}'
            elif licenca.data_fim and licenca.data_fim <= hoje + timedelta(days=days_warning):
                status_licenca = 'vencendo'
                dias_restantes = (licenca.data_fim - hoje).days
                mensagem = f'Licença vence em {dias_restantes} dias ({licenca.data_fim})'
            
            # Verifica limites de uso
            limites = self.check_usage_limits(empresa_id, licenca)
            
            return {
                'empresa_id': empresa.id,
                'empresa_nome': empresa.nome,
                'empresa_cnpj': empresa.cnpj,
                'licenca_tipo': licenca.tipo,
                'status': status_licenca,
                'mensagem': mensagem,
                'data_inicio': licenca.data_inicio,
                'data_fim': licenca.data_fim,
                'valor_mensal': float(licenca.valor_mensal) if licenca.valor_mensal else None,
                'limites': limites,
                'data_verificacao': datetime.now()
            }
            
        except Empresa.DoesNotExist:
            return None
    
    def check_usage_limits(self, empresa_id, licenca):
        """Verifica limites de uso da licença"""
        try:
            db_alias = get_empresa_database(empresa_id)
            
            # Verifica se o banco da empresa existe
            if db_alias not in connections.databases:
                return {
                    'erro': 'Banco da empresa não encontrado'
                }
            
            with connections[db_alias].cursor() as cursor:
                limites = {}
                
                # Conta funcionários
                try:
                    cursor.execute("SELECT COUNT(*) FROM escalator_funcionario WHERE ativo = 1")
                    funcionarios_ativos = cursor.fetchone()[0]
                    limites['funcionarios'] = {
                        'atual': funcionarios_ativos,
                        'limite': licenca.max_funcionarios,
                        'percentual_uso': (funcionarios_ativos / licenca.max_funcionarios * 100) if licenca.max_funcionarios else 0,
                        'excedeu': funcionarios_ativos > licenca.max_funcionarios if licenca.max_funcionarios else False
                    }
                except:
                    limites['funcionarios'] = {'erro': 'Tabela de funcionários não encontrada'}
                
                # Conta usuários
                try:
                    cursor.execute("SELECT COUNT(*) FROM usuarios_usuario WHERE is_active = 1")
                    usuarios_ativos = cursor.fetchone()[0]
                    limites['usuarios'] = {
                        'atual': usuarios_ativos,
                        'limite': licenca.max_usuarios,
                        'percentual_uso': (usuarios_ativos / licenca.max_usuarios * 100) if licenca.max_usuarios else 0,
                        'excedeu': usuarios_ativos > licenca.max_usuarios if licenca.max_usuarios else False
                    }
                except:
                    limites['usuarios'] = {'erro': 'Tabela de usuários não encontrada'}
                
                return limites
                
        except Exception as e:
            return {
                'erro': f'Erro ao verificar limites: {str(e)}'
            }
    
    def display_results(self, results):
        """Exibe resultados em formato texto"""
        if not results:
            self.stdout.write(
                self.style.WARNING('Nenhuma empresa encontrada ou nenhum problema detectado')
            )
            return
        
        self.stdout.write(f'\n=== RELATÓRIO DE LICENÇAS ({len(results)} empresas) ===\n')
        
        for result in results:
            # Cabeçalho da empresa
            self.stdout.write(f"Empresa: {result['empresa_nome']} (ID: {result['empresa_id']})")
            self.stdout.write(f"CNPJ: {result['empresa_cnpj']}")
            
            # Status da licença
            if result['status'] == 'ativa':
                style = self.style.SUCCESS
            elif result['status'] == 'vencendo':
                style = self.style.WARNING
            else:
                style = self.style.ERROR
            
            self.stdout.write(style(f"Status: {result['mensagem']}"))
            
            if 'licenca_tipo' in result:
                self.stdout.write(f"Tipo de Licença: {result['licenca_tipo']}")
                self.stdout.write(f"Período: {result['data_inicio']} até {result['data_fim']}")
                
                if result['valor_mensal']:
                    self.stdout.write(f"Valor Mensal: R$ {result['valor_mensal']:.2f}")
            
            # Limites de uso
            if 'limites' in result and 'erro' not in result['limites']:
                self.stdout.write("\nLimites de Uso:")
                
                for tipo, dados in result['limites'].items():
                    if 'erro' in dados:
                        self.stdout.write(f"  {tipo.title()}: {dados['erro']}")
                    else:
                        status_limite = "⚠️  EXCEDIDO" if dados['excedeu'] else "✅ OK"
                        self.stdout.write(
                            f"  {tipo.title()}: {dados['atual']}/{dados['limite']} "
                            f"({dados['percentual_uso']:.1f}%) {status_limite}"
                        )
            
            self.stdout.write("-" * 50)