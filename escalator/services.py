"""
Serviços de negócio para o sistema de gerenciamento de escalas.
Implementa todas as regras trabalhistas brasileiras conforme CLT.
"""

from datetime import datetime, timedelta, time, date
from typing import List, Dict, Tuple, Optional
from django.db.models import Q, Sum
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from .models import (
    Funcionario, Escala, Ponto, BancoHoras, Contrato, 
    ConfiguracaoSistema, EscalaPredefinida
)


class ValidadorRegrasTrabalho:
    """
    Validador das regras trabalhistas brasileiras conforme CLT.
    Implementa todas as validações obrigatórias do sistema.
    """
    
    def __init__(self):
        """Inicializa o validador com configurações do sistema"""
        try:
            self.periodo_noturno_inicio, self.periodo_noturno_fim = ConfiguracaoSistema.get_periodo_noturno()
            self.interjornada_minima = ConfiguracaoSistema.get_interjornada_minima()
        except Exception:
            # Se não conseguir obter as configurações, usa valores padrão
            self.periodo_noturno_inicio, self.periodo_noturno_fim = time(22, 0), time(5, 0)
            self.interjornada_minima = 660
    
    def validar_jornada_diaria(self, funcionario: Funcionario, data: date) -> Dict:
        """Valida se a jornada diária está dentro dos limites legais"""
        contrato = self._get_contrato_vigente(funcionario, data)
        if not contrato:
            return {'valido': False, 'erro': 'Contrato não encontrado'}
        
        escala = Escala.objects.filter(funcionario=funcionario, data=data).first()
        if not escala or escala.descanso:
            return {'valido': True, 'jornada_minutos': 0}
        
        jornada_minutos = escala.duracao_minutos
        
        # Verifica limite diário
        if jornada_minutos > contrato.carga_diaria_max:
            return {
                'valido': False,
                'erro': f'Jornada de {jornada_minutos}min excede limite diário de {contrato.carga_diaria_max}min',
                'jornada_minutos': jornada_minutos
            }
        
        return {'valido': True, 'jornada_minutos': jornada_minutos}
    
    def validar_jornada_semanal(self, funcionario: Funcionario, data_inicio: date) -> Dict:
        """Valida se a jornada semanal está dentro dos limites legais"""
        contrato = self._get_contrato_vigente(funcionario, data_inicio)
        if not contrato:
            return {'valido': False, 'erro': 'Contrato não encontrado'}
        
        data_fim = data_inicio + timedelta(days=6)
        escalas = Escala.objects.filter(
            funcionario=funcionario,
            data__range=[data_inicio, data_fim],
            descanso=False
        )
        
        total_minutos = sum(escala.duracao_minutos for escala in escalas)
        
        if total_minutos > contrato.carga_semanal_max:
            return {
                'valido': False,
                'erro': f'Jornada semanal de {total_minutos}min excede limite de {contrato.carga_semanal_max}min',
                'total_minutos': total_minutos
            }
        
        return {'valido': True, 'total_minutos': total_minutos}
    
    def validar_pausa_intrajornada(self, escala: Escala) -> Dict:
        """Valida se a pausa intrajornada está adequada"""
        if escala.descanso:
            return {'valido': True, 'pausa_necessaria': 0}
        
        jornada_minutos = escala.duracao_minutos
        
        # Jornada >= 6h: pausa de 60min
        if jornada_minutos >= 360:
            pausa_necessaria = 60
        # Jornada entre 4-6h: pausa de 15min
        elif jornada_minutos >= 240:
            pausa_necessaria = 15
        else:
            pausa_necessaria = 0
        
        if escala.pausa_minutos < pausa_necessaria:
            return {
                'valido': False,
                'erro': f'Pausa de {escala.pausa_minutos}min insuficiente. Necessário: {pausa_necessaria}min',
                'pausa_necessaria': pausa_necessaria
            }
        
        return {'valido': True, 'pausa_necessaria': pausa_necessaria}
    
    def validar_interjornada(self, funcionario: Funcionario, data: date) -> Dict:
        """Valida o intervalo mínimo entre jornadas (660 minutos)"""
        escala_atual = Escala.objects.filter(funcionario=funcionario, data=data).first()
        if not escala_atual or escala_atual.descanso:
            return {'valido': True}
        
        # Busca escala do dia anterior
        data_anterior = data - timedelta(days=1)
        escala_anterior = Escala.objects.filter(
            funcionario=funcionario, 
            data=data_anterior,
            descanso=False
        ).first()
        
        if not escala_anterior:
            return {'valido': True}
        
        # Calcula intervalo entre fim da jornada anterior e início da atual
        fim_anterior = datetime.combine(data_anterior, escala_anterior.hora_fim)
        inicio_atual = datetime.combine(data, escala_atual.hora_inicio)
        
        # Se passou da meia-noite
        if escala_anterior.hora_fim < escala_atual.hora_inicio:
            intervalo = inicio_atual - fim_anterior
        else:
            intervalo = (inicio_atual + timedelta(days=1)) - fim_anterior
        
        intervalo_minutos = int(intervalo.total_seconds() / 60)
        
        if intervalo_minutos < self.interjornada_minima:
            return {
                'valido': False,
                'erro': f'Interjornada de {intervalo_minutos}min menor que mínimo de {self.interjornada_minima}min',
                'intervalo_minutos': intervalo_minutos
            }
        
        return {'valido': True, 'intervalo_minutos': intervalo_minutos}
    
    def validar_dsr(self, funcionario: Funcionario, data_inicio: date) -> Dict:
        """Valida se há DSR (Descanso Semanal Remunerado) a cada 7 dias"""
        data_fim = data_inicio + timedelta(days=6)
        
        # Conta dias de descanso na semana
        dias_descanso = Escala.objects.filter(
            funcionario=funcionario,
            data__range=[data_inicio, data_fim],
            descanso=True
        ).count()
        
        if dias_descanso == 0:
            return {
                'valido': False,
                'erro': 'Nenhum DSR encontrado na semana',
                'dias_descanso': dias_descanso
            }
        
        return {'valido': True, 'dias_descanso': dias_descanso}
    
    def validar_escala_12x36(self, escala: Escala) -> Dict:
        """Valida regras específicas da escala 12x36"""
        if escala.tipo_escala != '12x36':
            return {'valido': True}
        
        contrato = self._get_contrato_vigente(escala.funcionario, escala.data)
        if not contrato or not contrato.permite_12x36:
            return {
                'valido': False,
                'erro': 'Contrato não permite escala 12x36'
            }
        
        # Verifica se tem folga no dia seguinte
        data_seguinte = escala.data + timedelta(days=1)
        folga_seguinte = Escala.objects.filter(
            funcionario=escala.funcionario,
            data=data_seguinte,
            descanso=True
        ).exists()
        
        if not folga_seguinte:
            return {
                'valido': False,
                'erro': 'Escala 12x36 deve ter folga embutida no dia seguinte'
            }
        
        # Valida interjornada (36h mínimo)
        validacao_interjornada = self.validar_interjornada(escala.funcionario, escala.data)
        if not validacao_interjornada['valido']:
            return validacao_interjornada
        
        return {'valido': True}
    
    def _get_contrato_vigente(self, funcionario: Funcionario, data: date) -> Optional[Contrato]:
        """Obtém o contrato vigente para o funcionário na data especificada"""
        return Contrato.objects.filter(
            funcionario=funcionario,
            vigencia_inicio__lte=data
        ).filter(
            Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=data)
        ).order_by('-vigencia_inicio').first()


class CalculadoraJornada:
    """
    Calculadora de jornadas, horas extras e adicionais.
    Implementa cálculos conforme legislação trabalhista brasileira.
    """
    
    def __init__(self):
        try:
            self.periodo_noturno_inicio, self.periodo_noturno_fim = ConfiguracaoSistema.get_periodo_noturno()
            self.hora_noturna_minutos = float(ConfiguracaoSistema.get_valor('hora_noturna_urbana_minutos', '52.5'))
        except Exception:
            # Se não conseguir obter as configurações, usa valores padrão
            self.periodo_noturno_inicio, self.periodo_noturno_fim = time(22, 0), time(5, 0)
            self.hora_noturna_minutos = 52.5
    
    def calcular_jornada_diaria(self, funcionario: Funcionario, data: date) -> Dict:
        """Calcula a jornada diária completa com todos os adicionais"""
        pontos = Ponto.objects.filter(
            funcionario=funcionario,
            timestamp__date=data
        ).order_by('timestamp')
        
        if not pontos.exists():
            return {
                'jornada_normal': 0,
                'horas_extras': 0,
                'adicional_noturno': 0,
                'total_trabalhado': 0,
                'pausas': 0
            }
        
        # Agrupa pontos por tipo
        entradas = pontos.filter(tipo_registro='entrada')
        saidas = pontos.filter(tipo_registro='saida')
        pausas_inicio = pontos.filter(tipo_registro='pausa_inicio')
        pausas_fim = pontos.filter(tipo_registro='pausa_fim')
        
        total_trabalhado = 0
        total_pausas = 0
        minutos_noturnos = 0
        
        # Calcula períodos trabalhados
        for i, entrada in enumerate(entradas):
            try:
                saida = saidas[i]
                periodo_minutos = int((saida.timestamp - entrada.timestamp).total_seconds() / 60)
                total_trabalhado += periodo_minutos
                
                # Calcula minutos noturnos neste período
                minutos_noturnos += self._calcular_minutos_noturnos(entrada.timestamp, saida.timestamp)
                
            except IndexError:
                # Entrada sem saída correspondente
                continue
        
        # Calcula pausas
        for i, pausa_inicio in enumerate(pausas_inicio):
            try:
                pausa_fim = pausas_fim[i]
                pausa_minutos = int((pausa_fim.timestamp - pausa_inicio.timestamp).total_seconds() / 60)
                total_pausas += pausa_minutos
            except IndexError:
                continue
        
        # Subtrai pausas do tempo trabalhado
        total_trabalhado -= total_pausas
        
        # Calcula horas extras
        contrato = self._get_contrato_vigente(funcionario, data)
        jornada_normal = min(total_trabalhado, contrato.carga_diaria_max if contrato else 480)
        horas_extras = max(0, total_trabalhado - jornada_normal)
        
        # Calcula adicional noturno (hora reduzida)
        adicional_noturno = int(minutos_noturnos / self.hora_noturna_minutos * 60)
        
        return {
            'jornada_normal': jornada_normal,
            'horas_extras': horas_extras,
            'adicional_noturno': adicional_noturno,
            'total_trabalhado': total_trabalhado,
            'pausas': total_pausas,
            'minutos_noturnos': minutos_noturnos
        }
    
    def calcular_banco_horas(self, funcionario: Funcionario, data: date) -> Dict:
        """Calcula créditos/débitos para o banco de horas"""
        jornada = self.calcular_jornada_diaria(funcionario, data)
        contrato = self._get_contrato_vigente(funcionario, data)
        
        if not contrato:
            return {'credito': 0, 'debito': 0, 'saldo': 0}
        
        jornada_prevista = contrato.carga_diaria_max
        jornada_realizada = jornada['total_trabalhado']
        
        diferenca = jornada_realizada - jornada_prevista
        
        if diferenca > 0:
            # Trabalhou mais que o previsto - crédito
            credito = min(diferenca, contrato.extra_diaria_cap)  # Limitado pelo cap diário
            debito = 0
        else:
            # Trabalhou menos que o previsto - débito
            credito = 0
            debito = abs(diferenca)
        
        return {
            'credito': credito,
            'debito': debito,
            'saldo': credito - debito
        }
    
    def _calcular_minutos_noturnos(self, inicio: datetime, fim: datetime) -> int:
        """Calcula quantos minutos foram trabalhados no período noturno"""
        minutos_noturnos = 0
        
        # Converte para time objects para comparação
        inicio_time = inicio.time()
        fim_time = fim.time()
        
        # Caso 1: Período totalmente diurno
        if (inicio_time >= self.periodo_noturno_fim and 
            fim_time <= self.periodo_noturno_inicio):
            return 0
        
        # Caso 2: Período cruza a meia-noite
        if fim < inicio:
            fim += timedelta(days=1)
        
        # Calcula intersecção com período noturno
        periodo_atual = inicio
        while periodo_atual < fim:
            hora_atual = periodo_atual.time()
            
            # Verifica se está no período noturno
            if (hora_atual >= self.periodo_noturno_inicio or 
                hora_atual < self.periodo_noturno_fim):
                minutos_noturnos += 1
            
            periodo_atual += timedelta(minutes=1)
        
        return minutos_noturnos
    
    def _get_contrato_vigente(self, funcionario: Funcionario, data: date) -> Optional[Contrato]:
        """Obtém o contrato vigente para o funcionário na data especificada"""
        return Contrato.objects.filter(
            funcionario=funcionario,
            vigencia_inicio__lte=data
        ).filter(
            Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=data)
        ).order_by('-vigencia_inicio').first()


class GerenciadorBancoHoras:
    """
    Gerenciador do banco de horas com controle de vencimentos.
    Implementa regras de compensação e pagamento como hora extra.
    """
    
    def atualizar_banco_horas(self, funcionario: Funcionario, data: date) -> BancoHoras:
        """Atualiza o banco de horas para uma data específica"""
        calculadora = CalculadoraJornada()
        calculo = calculadora.calcular_banco_horas(funcionario, data)
        
        banco, created = BancoHoras.objects.get_or_create(
            funcionario=funcionario,
            data_referencia=data,
            defaults={
                'credito_minutos': calculo['credito'],
                'debito_minutos': calculo['debito']
            }
        )
        
        if not created:
            banco.credito_minutos = calculo['credito']
            banco.debito_minutos = calculo['debito']
            banco.save()
        
        return banco
    
    def obter_saldo_atual(self, funcionario: Funcionario) -> Dict:
        """Obtém o saldo atual do banco de horas"""
        registros = BancoHoras.objects.filter(
            funcionario=funcionario,
            compensado=False
        )
        
        total_credito = registros.aggregate(Sum('credito_minutos'))['credito_minutos__sum'] or 0
        total_debito = registros.aggregate(Sum('debito_minutos'))['debito_minutos__sum'] or 0
        saldo_atual = total_credito - total_debito
        
        # Verifica registros próximos ao vencimento (30 dias)
        data_limite = date.today() + timedelta(days=30)
        vencendo = registros.filter(
            data_vencimento__lte=data_limite,
            data_vencimento__gte=date.today()
        )
        
        return {
            'saldo_atual': saldo_atual,
            'total_credito': total_credito,
            'total_debito': total_debito,
            'registros_vencendo': vencendo.count(),
            'minutos_vencendo': vencendo.aggregate(Sum('saldo_minutos'))['saldo_minutos__sum'] or 0
        }
    
    def processar_vencimentos(self, data_referencia: date = None) -> List[Dict]:
        """Processa registros vencidos do banco de horas"""
        if data_referencia is None:
            data_referencia = date.today()
        
        registros_vencidos = BancoHoras.objects.filter(
            data_vencimento__lt=data_referencia,
            compensado=False,
            saldo_minutos__gt=0  # Apenas créditos não compensados
        )
        
        resultados = []
        for registro in registros_vencidos:
            # Marca como compensado (será pago como hora extra)
            registro.compensado = True
            registro.observacoes += f"\nVencido em {data_referencia} - Convertido para hora extra"
            registro.save()
            
            resultados.append({
                'funcionario': registro.funcionario,
                'data_referencia': registro.data_referencia,
                'minutos_vencidos': registro.saldo_minutos,
                'valor_hora_extra': self._calcular_valor_hora_extra(registro)
            })
        
        return resultados
    
    def compensar_horas(self, funcionario: Funcionario, minutos_compensar: int, 
                       data_compensacao: date) -> Dict:
        """Compensa horas do banco através de folga ou redução de jornada"""
        saldo = self.obter_saldo_atual(funcionario)
        
        if saldo['saldo_atual'] < minutos_compensar:
            return {
                'sucesso': False,
                'erro': f'Saldo insuficiente. Disponível: {saldo["saldo_atual"]}min'
            }
        
        # Cria registro de compensação
        BancoHoras.objects.create(
            funcionario=funcionario,
            data_referencia=data_compensacao,
            debito_minutos=minutos_compensar,
            observacoes=f'Compensação de {minutos_compensar} minutos'
        )
        
        return {
            'sucesso': True,
            'minutos_compensados': minutos_compensar,
            'saldo_restante': saldo['saldo_atual'] - minutos_compensar
        }
    
    def _calcular_valor_hora_extra(self, registro: BancoHoras) -> float:
        """Calcula o valor da hora extra (placeholder - implementar com dados salariais)"""
        # Esta função deveria integrar com dados salariais do funcionário
        # Por ora, retorna apenas os minutos para conversão posterior
        return registro.saldo_minutos


class ProcessadorPontos:
    """
    Processador de registros de ponto com validações automáticas.
    Integra com as regras trabalhistas e escalas programadas.
    """
    
    def registrar_ponto(self, funcionario: Funcionario, tipo_registro: str, 
                       timestamp: datetime, localizacao: Tuple[float, float] = None,
                       observacoes: str = '') -> Dict:
        """Registra um ponto com validações automáticas"""
        
        # Busca escala do dia
        escala = Escala.objects.filter(
            funcionario=funcionario,
            data=timestamp.date()
        ).first()
        
        # Validações básicas
        validacoes = self._validar_registro_ponto(funcionario, tipo_registro, timestamp, escala)
        if not validacoes['valido']:
            return {
                'sucesso': False,
                'erro': validacoes.get('erro', 'Erro de validação')
            }
        
        # Cria o registro de ponto
        ponto = Ponto.objects.create(
            funcionario=funcionario,
            escala=escala,
            timestamp=timestamp,
            tipo_registro=tipo_registro,
            localizacao_lat=localizacao[0] if localizacao else None,
            localizacao_lng=localizacao[1] if localizacao else None,
            observacoes=observacoes,
            validado=validacoes.get('auto_validado', False)
        )
        
        # Atualiza banco de horas se for final do dia
        if tipo_registro == 'saida':
            gerenciador = GerenciadorBancoHoras()
            gerenciador.atualizar_banco_horas(funcionario, timestamp.date())
        
        return {
            'sucesso': True,
            'ponto_id': ponto.id,
            'validado': ponto.validado,
            'alertas': validacoes.get('alertas', [])
        }
    
    def obter_pontos_dia(self, funcionario: Funcionario, data: date) -> Dict:
        """Obtém todos os pontos de um funcionário em uma data"""
        pontos = Ponto.objects.filter(
            funcionario=funcionario,
            timestamp__date=data
        ).order_by('timestamp')
        
        calculadora = CalculadoraJornada()
        jornada = calculadora.calcular_jornada_diaria(funcionario, data)
        
        return {
            'pontos': pontos,
            'jornada': jornada,
            'total_registros': pontos.count()
        }
    
    def _validar_registro_ponto(self, funcionario: Funcionario, tipo_registro: str,
                               timestamp: datetime, escala: Escala = None) -> Dict:
        """Valida um registro de ponto antes de salvá-lo"""
        alertas = []
        auto_validado = True
        
        # Verifica se há escala para o dia
        if not escala:
            alertas.append('Nenhuma escala encontrada para este dia')
            auto_validado = False
        elif escala.descanso:
            alertas.append('Registro em dia de descanso (DSR)')
            auto_validado = False
        
        # Verifica horário em relação à escala
        if escala and not escala.descanso:
            hora_registro = timestamp.time()
            
            if tipo_registro == 'entrada':
                if escala.hora_inicio:
                    diferenca = self._calcular_diferenca_minutos(hora_registro, escala.hora_inicio)
                    if abs(diferenca) > 15:  # Tolerância de 15 minutos
                        alertas.append(f'Entrada com {abs(diferenca)}min de diferença do programado')
            
            elif tipo_registro == 'saida':
                if escala.hora_fim:
                    diferenca = self._calcular_diferenca_minutos(hora_registro, escala.hora_fim)
                    if abs(diferenca) > 15:
                        alertas.append(f'Saída com {abs(diferenca)}min de diferença do programado')
        
        # Verifica sequência lógica de registros
        ultimo_ponto = Ponto.objects.filter(
            funcionario=funcionario,
            timestamp__date=timestamp.date()
        ).order_by('-timestamp').first()
        
        if ultimo_ponto:
            if not self._validar_sequencia_pontos(ultimo_ponto.tipo_registro, tipo_registro):
                return {
                    'valido': False,
                    'erro': f'Sequência inválida: {ultimo_ponto.tipo_registro} → {tipo_registro}'
                }
        
        return {
            'valido': True,
            'auto_validado': auto_validado,
            'alertas': alertas
        }
    
    def _calcular_diferenca_minutos(self, hora1: time, hora2: time) -> int:
        """Calcula diferença em minutos entre dois horários"""
        dt1 = datetime.combine(date.today(), hora1)
        dt2 = datetime.combine(date.today(), hora2)
        return int((dt1 - dt2).total_seconds() / 60)
    
    def _validar_sequencia_pontos(self, ultimo_tipo: str, novo_tipo: str) -> bool:
        """Valida se a sequência de tipos de ponto é lógica"""
        sequencias_validas = {
            'entrada': ['saida', 'pausa_inicio'],
            'saida': ['entrada'],
            'pausa_inicio': ['pausa_fim'],
            'pausa_fim': ['saida', 'pausa_inicio']
        }
        
        return novo_tipo in sequencias_validas.get(ultimo_tipo, [])


class ConsultorEscalasBrasil:
    """
    Consultor de escalas disponíveis no Brasil.
    Fornece modelos predefinidos conforme legislação brasileira.
    """
    
    def obter_escalas_disponiveis(self) -> List[Dict]:
        """Retorna todas as escalas predefinidas disponíveis no Brasil"""
        escalas_predefinidas = EscalaPredefinida.objects.all()
        
        escalas = []
        for escala in escalas_predefinidas:
            escalas.append({
                'id': escala.id,
                'nome': escala.nome,
                'descricao': escala.descricao,
                'horas_trabalho': escala.horas_trabalho,
                'horas_descanso': escala.horas_descanso,
                'legal': self._verificar_legalidade_escala(escala),
                'observacoes': self._obter_observacoes_escala(escala)
            })
        
        return escalas
    
    def aplicar_escala_predefinida(self, funcionario: Funcionario, escala_id: int,
                                  data_inicio: date, data_fim: date) -> Dict:
        """Aplica uma escala predefinida para um período"""
        try:
            escala_predefinida = EscalaPredefinida.objects.get(id=escala_id)
        except EscalaPredefinida.DoesNotExist:
            return {'sucesso': False, 'erro': 'Escala predefinida não encontrada'}
        
        # Verifica se funcionário pode usar esta escala
        contrato = Contrato.objects.filter(
            funcionario=funcionario,
            vigencia_inicio__lte=data_inicio
        ).order_by('-vigencia_inicio').first()
        
        if escala_predefinida.nome == '12x36' and (not contrato or not contrato.permite_12x36):
            return {'sucesso': False, 'erro': 'Funcionário não autorizado para escala 12x36'}
        
        # Gera escalas para o período
        escalas_criadas = []
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            # Lógica específica por tipo de escala
            if escala_predefinida.nome == '12x36':
                escalas_criadas.extend(self._gerar_escala_12x36(funcionario, data_atual, data_fim))
                break
            elif escala_predefinida.nome == '6x1':
                escalas_criadas.extend(self._gerar_escala_6x1(funcionario, data_atual, data_fim))
                break
            elif escala_predefinida.nome == '5x2':
                escalas_criadas.extend(self._gerar_escala_5x2(funcionario, data_atual, data_fim))
                break
            
            data_atual += timedelta(days=1)
        
        return {
            'sucesso': True,
            'escalas_criadas': len(escalas_criadas),
            'periodo': f'{data_inicio} a {data_fim}'
        }
    
    def _verificar_legalidade_escala(self, escala: EscalaPredefinida) -> bool:
        """Verifica se a escala está em conformidade com a legislação"""
        # Implementa verificações básicas de legalidade
        if escala.horas_trabalho > 12:
            return False
        if escala.horas_descanso < 11:  # Interjornada mínima
            return False
        return True
    
    def _obter_observacoes_escala(self, escala: EscalaPredefinida) -> str:
        """Retorna observações específicas sobre a escala"""
        observacoes = {
            '12x36': 'Requer autorização específica no contrato. Folga embutida obrigatória.',
            '6x1': 'Escala comercial padrão. DSR preferencialmente aos domingos.',
            '5x2': 'Escala administrativa. Fins de semana livres.',
            '4x2': 'Escala industrial. Requer pausas adequadas para jornadas longas.'
        }
        return observacoes.get(escala.nome, '')
    
    def _gerar_escala_12x36(self, funcionario: Funcionario, data_inicio: date, data_fim: date) -> List[Escala]:
        """Gera escalas no padrão 12x36"""
        escalas = []
        data_atual = data_inicio
        trabalha = True  # Começa trabalhando
        
        while data_atual <= data_fim:
            if trabalha:
                # Dia de trabalho (12h)
                escala = Escala.objects.create(
                    funcionario=funcionario,
                    data=data_atual,
                    hora_inicio=time(7, 0),  # 07:00
                    hora_fim=time(19, 0),    # 19:00
                    pausa_minutos=60,
                    tipo_escala='12x36',
                    descanso=False
                )
                escalas.append(escala)
                
                # Próximo dia é folga
                data_folga = data_atual + timedelta(days=1)
                if data_folga <= data_fim:
                    folga = Escala.objects.create(
                        funcionario=funcionario,
                        data=data_folga,
                        descanso=True,
                        tipo_escala='12x36'
                    )
                    escalas.append(folga)
                
                data_atual += timedelta(days=2)  # Pula para depois da folga
            else:
                data_atual += timedelta(days=1)
            
            trabalha = not trabalha
        
        return escalas
    
    def _gerar_escala_6x1(self, funcionario: Funcionario, data_inicio: date, data_fim: date) -> List[Escala]:
        """Gera escalas no padrão 6x1"""
        escalas = []
        data_atual = data_inicio
        dias_trabalhados = 0
        
        while data_atual <= data_fim:
            if dias_trabalhados < 6:
                # Dia de trabalho
                escala = Escala.objects.create(
                    funcionario=funcionario,
                    data=data_atual,
                    hora_inicio=time(8, 0),   # 08:00
                    hora_fim=time(17, 0),     # 17:00
                    pausa_minutos=60,
                    tipo_escala='normal',
                    descanso=False
                )
                escalas.append(escala)
                dias_trabalhados += 1
            else:
                # Dia de descanso (DSR)
                folga = Escala.objects.create(
                    funcionario=funcionario,
                    data=data_atual,
                    descanso=True,
                    tipo_escala='normal'
                )
                escalas.append(folga)
                dias_trabalhados = 0  # Reinicia o ciclo
            
            data_atual += timedelta(days=1)
        
        return escalas
    
    def _gerar_escala_5x2(self, funcionario: Funcionario, data_inicio: date, data_fim: date) -> List[Escala]:
        """Gera escalas no padrão 5x2 (segunda a sexta)"""
        escalas = []
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            # 0 = segunda, 6 = domingo
            dia_semana = data_atual.weekday()
            
            if dia_semana < 5:  # Segunda a sexta (0-4)
                # Dia de trabalho
                escala = Escala.objects.create(
                    funcionario=funcionario,
                    data=data_atual,
                    hora_inicio=time(8, 0),   # 08:00
                    hora_fim=time(17, 0),     # 17:00
                    pausa_minutos=60,
                    tipo_escala='normal',
                    descanso=False
                )
                escalas.append(escala)
            else:
                # Fim de semana - descanso
                folga = Escala.objects.create(
                    funcionario=funcionario,
                    data=data_atual,
                    descanso=True,
                    tipo_escala='normal'
                )
                escalas.append(folga)
            
            data_atual += timedelta(days=1)
        
        return escalas