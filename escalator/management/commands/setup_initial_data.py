"""
Comando Django para configurar dados iniciais do sistema de escalas.
Cria escalas predefinidas e configurações do sistema.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from escalator.models import EscalaPredefinida, ConfiguracaoSistema
import datetime


class Command(BaseCommand):
    help = 'Configura dados iniciais do sistema de escalas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando configuração de dados iniciais...'))
        
        # Criar escalas predefinidas
        self._criar_escalas_predefinidas()
        
        # Criar configurações do sistema
        self._criar_configuracoes_sistema()
        
        self.stdout.write(self.style.SUCCESS('Dados iniciais configurados com sucesso!'))

    def _criar_escalas_predefinidas(self):
        """Cria escalas predefinidas padrão."""
        escalas = [
            {
                'nome': 'Escala 12x36',
                'descricao': 'Escala de 12 horas de trabalho por 36 horas de descanso',
                'horas_trabalho': 12,
                'horas_descanso': 36
            },
            {
                'nome': 'Escala 6x1',
                'descricao': 'Escala de 6 dias de trabalho por 1 dia de folga',
                'horas_trabalho': 8,
                'horas_descanso': 24
            },
            {
                'nome': 'Escala 5x2',
                'descricao': 'Escala de 5 dias de trabalho por 2 dias de folga',
                'horas_trabalho': 8,
                'horas_descanso': 48
            },
            {
                'nome': 'Escala 4x2',
                'descricao': 'Escala de 4 dias de trabalho por 2 dias de folga',
                'horas_trabalho': 8,
                'horas_descanso': 48
            },
            {
                'nome': 'Escala Noturna 12x36',
                'descricao': 'Escala noturna de 12 horas por 36 horas de descanso',
                'horas_trabalho': 12,
                'horas_descanso': 36
            }
        ]
        
        for escala_data in escalas:
            escala, created = EscalaPredefinida.objects.get_or_create(
                nome=escala_data['nome'],
                defaults=escala_data
            )
            if created:
                self.stdout.write(f'Criada escala predefinida: {escala.nome}')
            else:
                self.stdout.write(f'Escala predefinida já existe: {escala.nome}')

    def _criar_configuracoes_sistema(self):
        """Cria configurações padrão do sistema."""
        configuracoes = [
            # Jornada de trabalho
            {
                'chave': 'jornada_maxima_diaria',
                'valor': '8',
                'descricao': 'Jornada máxima diária em horas (padrão CLT)'
            },
            {
                'chave': 'jornada_maxima_semanal',
                'valor': '44',
                'descricao': 'Jornada máxima semanal em horas (padrão CLT)'
            },
            {
                'chave': 'jornada_maxima_diaria_12x36',
                'valor': '12',
                'descricao': 'Jornada máxima diária para escala 12x36'
            },
            
            # Pausas e intervalos
            {
                'chave': 'pausa_minima_6h',
                'valor': '15',
                'descricao': 'Pausa mínima para jornada de 6 horas (em minutos)'
            },
            {
                'chave': 'pausa_minima_8h',
                'valor': '60',
                'descricao': 'Pausa mínima para jornada de 8 horas (em minutos)'
            },
            {
                'chave': 'interjornada_minima',
                'valor': '660',
                'descricao': 'Intervalo mínimo entre jornadas em minutos (11 horas)'
            },
            
            # Período noturno
            {
                'chave': 'periodo_noturno_inicio',
                'valor': '22:00',
                'descricao': 'Horário de início do período noturno'
            },
            {
                'chave': 'periodo_noturno_fim',
                'valor': '05:00',
                'descricao': 'Horário de fim do período noturno'
            },
            {
                'chave': 'hora_noturna_minutos',
                'valor': '52.5',
                'descricao': 'Duração da hora noturna em minutos (52min30s)'
            },
            {
                'chave': 'adicional_noturno_percentual',
                'valor': '20',
                'descricao': 'Percentual do adicional noturno'
            },
            
            # Banco de horas
            {
                'chave': 'banco_horas_prazo_meses',
                'valor': '12',
                'descricao': 'Prazo para compensação do banco de horas em meses'
            },
            {
                'chave': 'banco_horas_limite_mensal',
                'valor': '10',
                'descricao': 'Limite mensal de horas no banco de horas'
            },
            
            # DSR e folgas
            {
                'chave': 'dsr_obrigatorio',
                'valor': 'true',
                'descricao': 'DSR obrigatório (Descanso Semanal Remunerado)'
            },
            {
                'chave': 'dsr_minimo_horas',
                'valor': '24',
                'descricao': 'Horas mínimas de DSR'
            },
            
            # Horas extras
            {
                'chave': 'hora_extra_limite_diario',
                'valor': '2',
                'descricao': 'Limite diário de horas extras'
            },
            {
                'chave': 'hora_extra_percentual_50',
                'valor': '50',
                'descricao': 'Percentual de hora extra (primeiras 2 horas)'
            },
            {
                'chave': 'hora_extra_percentual_100',
                'valor': '100',
                'descricao': 'Percentual de hora extra (acima de 2 horas)'
            },
            
            # Tolerância de ponto
            {
                'chave': 'tolerancia_ponto_minutos',
                'valor': '10',
                'descricao': 'Tolerância para marcação de ponto em minutos'
            },
            
            # Configurações de sistema
            {
                'chave': 'sistema_versao',
                'valor': '1.0.0',
                'descricao': 'Versão do sistema de escalas'
            },
            {
                'chave': 'empresa_nome',
                'valor': 'Empresa Exemplo',
                'descricao': 'Nome da empresa'
            }
        ]
        
        for config_data in configuracoes:
            config, created = ConfiguracaoSistema.objects.get_or_create(
                chave=config_data['chave'],
                defaults={
                    'valor': config_data['valor'],
                    'descricao': config_data['descricao']
                }
            )
            if created:
                self.stdout.write(f'Criada configuração: {config.chave}')
            else:
                self.stdout.write(f'Configuração já existe: {config.chave}')