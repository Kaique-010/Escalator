"""
ViewSets Django REST Framework para o sistema de gerenciamento de escalas.
Implementa todas as APIs REST conforme especificação técnica.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import date, datetime, timedelta
from typing import Dict, List

from .models import (
    Funcionario, Escala, Ponto, BancoHoras, Contrato, 
    ConfiguracaoSistema, EscalaPredefinida, Folga
)
from .serializers import (
    FuncionarioSerializer, EscalaSerializer, PontoSerializer,
    BancoHorasSerializer, ContratoSerializer, ConfiguracaoSistemaSerializer,
    EscalaPredefinidaSerializer, FolgaSerializer, SaldoBancoHorasSerializer,
    CompensacaoHorasSerializer, RelatorioJornadaSerializer, ValidacaoEscalaSerializer
)
from .services import (
    ValidadorRegrasTrabalho, CalculadoraJornada, 
    GerenciadorBancoHoras, ProcessadorPontos, ConsultorEscalasBrasil
)


class FuncionarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de funcionários.
    Fornece operações CRUD e consultas específicas.
    """
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['ativo', 'cargo']
    search_fields = ['nome', 'user__email', 'cargo']
    ordering_fields = ['nome', 'data_admissao', 'created_at']
    ordering = ['nome']
    
    @action(detail=True, methods=['get'])
    def escalas_mes(self, request, pk=None):
        """Retorna escalas do funcionário para o mês atual ou especificado"""
        funcionario = self.get_object()
        
        # Parâmetros de data
        ano = int(request.query_params.get('ano', date.today().year))
        mes = int(request.query_params.get('mes', date.today().month))
        
        # Primeiro e último dia do mês
        primeiro_dia = date(ano, mes, 1)
        if mes == 12:
            ultimo_dia = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(ano, mes + 1, 1) - timedelta(days=1)
        
        escalas = Escala.objects.filter(
            funcionario=funcionario,
            data__range=[primeiro_dia, ultimo_dia]
        ).order_by('data')
        
        serializer = EscalaSerializer(escalas, many=True)
        
        return Response({
            'funcionario': funcionario.nome,
            'periodo': f'{primeiro_dia} a {ultimo_dia}',
            'total_escalas': escalas.count(),
            'escalas': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def saldo_banco_horas(self, request, pk=None):
        """Retorna saldo atual do banco de horas do funcionário"""
        funcionario = self.get_object()
        gerenciador = GerenciadorBancoHoras()
        saldo = gerenciador.obter_saldo_atual(funcionario)
        
        serializer = SaldoBancoHorasSerializer({
            'funcionario': funcionario,
            **saldo
        })
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def compensar_horas(self, request, pk=None):
        """Compensa horas do banco de horas"""
        funcionario = self.get_object()
        
        data = request.data.copy()
        data['funcionario'] = funcionario.id
        
        serializer = CompensacaoHorasSerializer(data=data)
        if serializer.is_valid():
            resultado = serializer.save()
            return Response(resultado, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContratoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de contratos de trabalho.
    Implementa validações trabalhistas brasileiras.
    """
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['funcionario', 'tipo_contrato', 'permite_12x36']
    search_fields = ['funcionario__nome']
    ordering_fields = ['vigencia_inicio', 'created_at']
    ordering = ['-vigencia_inicio']
    
    @action(detail=False, methods=['get'])
    def vigentes(self, request):
        """Retorna apenas contratos vigentes"""
        hoje = date.today()
        contratos_vigentes = self.queryset.filter(
            vigencia_inicio__lte=hoje
        ).filter(
            Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=hoje)
        )
        
        serializer = self.get_serializer(contratos_vigentes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def validar_conformidade(self, request, pk=None):
        """Valida conformidade do contrato com a legislação trabalhista"""
        contrato = self.get_object()
        
        validacoes = {
            'carga_diaria_valida': contrato.carga_diaria_max <= 720,  # 12h
            'carga_semanal_valida': contrato.carga_semanal_max <= 2640,  # 44h
            'extra_diaria_valida': contrato.extra_diaria_cap <= 120,  # 2h
            'banco_horas_valido': contrato.banco_horas_prazo_meses <= 12,
            'vigencia_valida': contrato.is_vigente()
        }
        
        todas_validas = all(validacoes.values())
        
        return Response({
            'contrato_id': contrato.id,
            'funcionario': contrato.funcionario.nome,
            'conforme': todas_validas,
            'validacoes': validacoes
        })


class EscalaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de escalas de trabalho.
    Implementa validações das regras trabalhistas brasileiras.
    """
    queryset = Escala.objects.all()
    serializer_class = EscalaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['funcionario', 'data', 'tipo_escala', 'descanso']
    search_fields = ['funcionario__nome']
    ordering_fields = ['data', 'hora_inicio', 'created_at']
    ordering = ['-data']
    
    @action(detail=False, methods=['get'])
    def periodo(self, request):
        """Retorna escalas de um período específico"""
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        funcionario_id = request.query_params.get('funcionario')
        
        if not data_inicio or not data_fim:
            return Response(
                {'erro': 'Parâmetros data_inicio e data_fim são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.queryset.filter(
            data__range=[data_inicio, data_fim]
        )
        
        if funcionario_id:
            queryset = queryset.filter(funcionario_id=funcionario_id)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'periodo': f'{data_inicio} a {data_fim}',
            'total_escalas': queryset.count(),
            'escalas': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def validar_periodo(self, request):
        """Valida escalas de um período conforme regras trabalhistas"""
        serializer = ValidacaoEscalaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        funcionario = serializer.validated_data['funcionario']
        data_inicio = serializer.validated_data['data_inicio']
        data_fim = serializer.validated_data['data_fim']
        
        validador = ValidadorRegrasTrabalho()
        escalas = Escala.objects.filter(
            funcionario=funcionario,
            data__range=[data_inicio, data_fim]
        ).order_by('data')
        
        escalas_validas = []
        escalas_invalidas = []
        violacoes = {
            'jornada_diaria': 0,
            'jornada_semanal': 0,
            'pausa_intrajornada': 0,
            'interjornada': 0,
            'dsr': 0
        }
        
        for escala in escalas:
            if escala.descanso:
                escalas_validas.append({
                    'data': escala.data,
                    'tipo': 'descanso'
                })
                continue
            
            # Validações individuais
            val_jornada = validador.validar_jornada_diaria(funcionario, escala.data)
            val_pausa = validador.validar_pausa_intrajornada(escala)
            val_interjornada = validador.validar_interjornada(funcionario, escala.data)
            
            erros = []
            if not val_jornada['valido']:
                erros.append(val_jornada['erro'])
                violacoes['jornada_diaria'] += 1
            
            if not val_pausa['valido']:
                erros.append(val_pausa['erro'])
                violacoes['pausa_intrajornada'] += 1
            
            if not val_interjornada['valido']:
                erros.append(val_interjornada['erro'])
                violacoes['interjornada'] += 1
            
            if erros:
                escalas_invalidas.append({
                    'data': escala.data,
                    'erros': erros
                })
            else:
                escalas_validas.append({
                    'data': escala.data,
                    'duracao_minutos': escala.duracao_minutos
                })
        
        # Valida DSR semanal
        data_atual = data_inicio
        while data_atual <= data_fim:
            val_dsr = validador.validar_dsr(funcionario, data_atual)
            if not val_dsr['valido']:
                violacoes['dsr'] += 1
            data_atual += timedelta(days=7)
        
        return Response({
            'funcionario': funcionario.nome,
            'periodo': f'{data_inicio} a {data_fim}',
            'escalas_validas': escalas_validas,
            'escalas_invalidas': escalas_invalidas,
            'resumo_violacoes': violacoes,
            'total_violacoes': sum(violacoes.values())
        })
    
    @action(detail=False, methods=['post'])
    def aplicar_escala_predefinida(self, request):
        """Aplica uma escala predefinida para um funcionário em um período"""
        funcionario_id = request.data.get('funcionario')
        escala_predefinida_id = request.data.get('escala_predefinida')
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        
        if not all([funcionario_id, escala_predefinida_id, data_inicio, data_fim]):
            return Response(
                {'erro': 'Todos os parâmetros são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except (Funcionario.DoesNotExist, ValueError) as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultor = ConsultorEscalasBrasil()
        resultado = consultor.aplicar_escala_predefinida(
            funcionario, escala_predefinida_id, data_inicio, data_fim
        )
        
        if resultado['sucesso']:
            return Response(resultado, status=status.HTTP_201_CREATED)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)


class PontoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de registros de ponto.
    Implementa validações automáticas e integração com escalas.
    """
    queryset = Ponto.objects.all()
    serializer_class = PontoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['funcionario', 'tipo_registro', 'validado']
    search_fields = ['funcionario__nome', 'observacoes']
    ordering_fields = ['timestamp', 'created_at']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def dia(self, request):
        """Retorna pontos de um funcionário em uma data específica"""
        funcionario_id = request.query_params.get('funcionario')
        data = request.query_params.get('data')
        
        if not funcionario_id or not data:
            return Response(
                {'erro': 'Parâmetros funcionario e data são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
            data_obj = datetime.strptime(data, '%Y-%m-%d').date()
        except (Funcionario.DoesNotExist, ValueError) as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        processador = ProcessadorPontos()
        resultado = processador.obter_pontos_dia(funcionario, data_obj)
        
        pontos_serializer = PontoSerializer(resultado['pontos'], many=True)
        
        return Response({
            'funcionario': funcionario.nome,
            'data': data,
            'pontos': pontos_serializer.data,
            'jornada': resultado['jornada'],
            'total_registros': resultado['total_registros']
        })
    
    @action(detail=False, methods=['post'])
    def registrar(self, request):
        """Registra um novo ponto com validações automáticas"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            ponto = serializer.save()
            return Response(
                PontoSerializer(ponto).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def periodo(self, request):
        """Retorna pontos de um período específico"""
        funcionario_id = request.query_params.get('funcionario')
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        
        if not all([funcionario_id, data_inicio, data_fim]):
            return Response(
                {'erro': 'Parâmetros funcionario, data_inicio e data_fim são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.queryset.filter(
            funcionario_id=funcionario_id,
            timestamp__date__range=[data_inicio, data_fim]
        )
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'periodo': f'{data_inicio} a {data_fim}',
            'total_pontos': queryset.count(),
            'pontos': serializer.data
        })


class BancoHorasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento do banco de horas.
    Implementa controle de vencimentos e compensações.
    """
    queryset = BancoHoras.objects.all()
    serializer_class = BancoHorasSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['funcionario', 'compensado']
    search_fields = ['funcionario__nome', 'observacoes']
    ordering_fields = ['data_referencia', 'data_vencimento', 'created_at']
    ordering = ['-data_referencia']
    
    @action(detail=False, methods=['get'])
    def saldos(self, request):
        """Retorna saldos de banco de horas de todos os funcionários"""
        funcionarios = Funcionario.objects.filter(ativo=True)
        gerenciador = GerenciadorBancoHoras()
        
        saldos = []
        for funcionario in funcionarios:
            saldo = gerenciador.obter_saldo_atual(funcionario)
            saldos.append({
                'funcionario_id': funcionario.id,
                'funcionario_nome': funcionario.nome,
                **saldo
            })
        
        return Response({
            'total_funcionarios': len(saldos),
            'saldos': saldos
        })
    
    @action(detail=False, methods=['get'])
    def vencimentos(self, request):
        """Retorna registros próximos ao vencimento"""
        dias_antecedencia = int(request.query_params.get('dias', 30))
        data_limite = date.today() + timedelta(days=dias_antecedencia)
        
        registros_vencendo = self.queryset.filter(
            data_vencimento__lte=data_limite,
            data_vencimento__gte=date.today(),
            compensado=False,
            saldo_minutos__gt=0
        ).order_by('data_vencimento')
        
        serializer = self.get_serializer(registros_vencendo, many=True)
        
        return Response({
            'dias_antecedencia': dias_antecedencia,
            'total_registros': registros_vencendo.count(),
            'registros_vencendo': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def processar_vencimentos(self, request):
        """Processa registros vencidos do banco de horas"""
        data_referencia = request.data.get('data_referencia')
        if data_referencia:
            data_referencia = datetime.strptime(data_referencia, '%Y-%m-%d').date()
        
        gerenciador = GerenciadorBancoHoras()
        resultados = gerenciador.processar_vencimentos(data_referencia)
        
        return Response({
            'data_processamento': data_referencia or date.today(),
            'registros_processados': len(resultados),
            'resultados': resultados
        })


class ConfiguracaoSistemaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configurações do sistema.
    Permite ajustar parâmetros das regras trabalhistas.
    """
    queryset = ConfiguracaoSistema.objects.all()
    serializer_class = ConfiguracaoSistemaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['chave', 'descricao']
    
    @action(detail=False, methods=['get'])
    def periodo_noturno(self, request):
        """Retorna configuração do período noturno"""
        inicio, fim = ConfiguracaoSistema.get_periodo_noturno()
        
        return Response({
            'periodo_noturno_inicio': inicio.strftime('%H:%M'),
            'periodo_noturno_fim': fim.strftime('%H:%M'),
            'descricao': 'Período noturno conforme CLT (22:00 às 05:00)'
        })
    
    @action(detail=False, methods=['get'])
    def interjornada(self, request):
        """Retorna configuração da interjornada mínima"""
        interjornada = ConfiguracaoSistema.get_interjornada_minima()
        
        return Response({
            'interjornada_minima_minutos': interjornada,
            'interjornada_minima_horas': interjornada / 60,
            'descricao': 'Interjornada mínima conforme CLT (11 horas)'
        })


class EscalaPredefinidaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para escalas predefinidas disponíveis no Brasil.
    Fornece modelos de escalas conforme legislação brasileira.
    """
    queryset = EscalaPredefinida.objects.all()
    serializer_class = EscalaPredefinidaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'horas_trabalho']
    ordering = ['nome']
    
    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        """Retorna todas as escalas disponíveis com análise de legalidade"""
        consultor = ConsultorEscalasBrasil()
        escalas = consultor.obter_escalas_disponiveis()
        
        return Response({
            'total_escalas': len(escalas),
            'escalas_disponiveis': escalas
        })


class FolgaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de folgas (compatibilidade).
    Mantém compatibilidade com sistema anterior.
    """
    queryset = Folga.objects.all()
    serializer_class = FolgaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['funcionario', 'data']
    search_fields = ['funcionario__nome', 'motivo']
    ordering_fields = ['data', 'created_at']
    ordering = ['-data']


class RelatoriosViewSet(viewsets.ViewSet):
    """
    ViewSet para relatórios e análises do sistema de escalas.
    Fornece dados consolidados e métricas de conformidade.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def jornada_funcionario(self, request):
        """Gera relatório de jornada de um funcionário"""
        serializer = RelatorioJornadaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        funcionario = serializer.validated_data['funcionario']
        data_inicio = serializer.validated_data['data_inicio']
        data_fim = serializer.validated_data['data_fim']
        
        calculadora = CalculadoraJornada()
        
        # Coleta dados do período
        data_atual = data_inicio
        total_dias = 0
        dias_trabalhados = 0
        dias_descanso = 0
        total_horas_normais = 0
        total_horas_extras = 0
        total_adicional_noturno = 0
        
        while data_atual <= data_fim:
            total_dias += 1
            
            escala = Escala.objects.filter(
                funcionario=funcionario,
                data=data_atual
            ).first()
            
            if escala:
                if escala.descanso:
                    dias_descanso += 1
                else:
                    dias_trabalhados += 1
                    jornada = calculadora.calcular_jornada_diaria(funcionario, data_atual)
                    total_horas_normais += jornada['jornada_normal']
                    total_horas_extras += jornada['horas_extras']
                    total_adicional_noturno += jornada['adicional_noturno']
            
            data_atual += timedelta(days=1)
        
        resultado = {
            'funcionario': funcionario,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'total_dias': total_dias,
            'dias_trabalhados': dias_trabalhados,
            'dias_descanso': dias_descanso,
            'total_horas_normais': total_horas_normais,
            'total_horas_extras': total_horas_extras,
            'total_adicional_noturno': total_adicional_noturno
        }
        
        response_serializer = RelatorioJornadaSerializer(resultado)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Retorna dados para dashboard do sistema"""
        hoje = date.today()
        
        # Funcionários ativos
        funcionarios_ativos = Funcionario.objects.filter(ativo=True).count()
        
        # Escalas de hoje
        escalas_hoje = Escala.objects.filter(data=hoje)
        trabalhando_hoje = escalas_hoje.filter(descanso=False).count()
        descansando_hoje = escalas_hoje.filter(descanso=True).count()
        
        # Pontos de hoje
        pontos_hoje = Ponto.objects.filter(timestamp__date=hoje).count()
        pontos_pendentes = Ponto.objects.filter(
            timestamp__date=hoje,
            validado=False
        ).count()
        
        # Banco de horas - registros vencendo
        data_limite = hoje + timedelta(days=30)
        registros_vencendo = BancoHoras.objects.filter(
            data_vencimento__lte=data_limite,
            data_vencimento__gte=hoje,
            compensado=False
        ).count()
        
        return Response({
            'data_referencia': hoje,
            'funcionarios_ativos': funcionarios_ativos,
            'trabalhando_hoje': trabalhando_hoje,
            'descansando_hoje': descansando_hoje,
            'pontos_hoje': pontos_hoje,
            'pontos_pendentes': pontos_pendentes,
            'registros_vencendo': registros_vencendo
        })
