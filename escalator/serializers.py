"""
Serializers Django REST Framework para o sistema de gerenciamento de escalas.
Implementa validações das regras trabalhistas brasileiras.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, datetime, timedelta
from typing import Dict, Any

from .models import (
    Funcionario, Escala, Ponto, BancoHoras, Contrato, 
    ConfiguracaoSistema, EscalaPredefinida, Folga
)
from .services import (
    ValidadorRegrasTrabalho, CalculadoraJornada, 
    GerenciadorBancoHoras, ProcessadorPontos
)

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer customizado para incluir dados do usuário na resposta do token"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Adiciona dados do usuário à resposta
        data['user'] = {
            'id': str(self.user.id),
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        return data


class FuncionarioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Funcionario"""
    
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    usuario_first_name = serializers.CharField(source='usuario.first_name', read_only=True)
    usuario_last_name = serializers.CharField(source='usuario.last_name', read_only=True)
    contrato_vigente = serializers.SerializerMethodField()
    
    class Meta:
        model = Funcionario
        fields = [
            'id', 'usuario', 'usuario_email', 'usuario_first_name', 'usuario_last_name',
            'nome', 'matricula', 'cargo', 'ativo',
            'contrato_vigente', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_contrato_vigente(self, obj):
        """Retorna o contrato vigente do funcionário"""
        contrato = Contrato.objects.filter(
            funcionario=obj,
            vigencia_inicio__lte=date.today()
        ).order_by('-vigencia_inicio').first()
        
        if contrato and contrato.is_vigente():
            return ContratoSerializer(contrato).data
        return None
    
    def validate_data_admissao(self, value):
        """Valida se a data de admissão não é futura"""
        if value > date.today():
            raise serializers.ValidationError("Data de admissão não pode ser futura")
        return value


class ContratoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Contrato com validações trabalhistas"""
    
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    vigente = serializers.SerializerMethodField()
    
    class Meta:
        model = Contrato
        fields = [
            'id', 'funcionario', 'funcionario_nome', 'tipo_contrato',
            'carga_diaria_max', 'carga_semanal_max', 'extra_diaria_cap',
            'banco_horas_prazo_meses', 'permite_12x36', 'vigencia_inicio',
            'vigencia_fim', 'vigente', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_vigente(self, obj):
        """Verifica se o contrato está vigente"""
        return obj.is_vigente()
    
    def validate(self, data):
        """Validações gerais do contrato"""
        # Valida carga horária diária (máximo 12h conforme CLT)
        if data.get('carga_diaria_max', 0) > 720:  # 12 horas em minutos
            raise serializers.ValidationError({
                'carga_diaria_max': 'Carga diária não pode exceder 12 horas (720 minutos)'
            })
        
        # Valida carga horária semanal (máximo 44h conforme CLT)
        if data.get('carga_semanal_max', 0) > 2640:  # 44 horas em minutos
            raise serializers.ValidationError({
                'carga_semanal_max': 'Carga semanal não pode exceder 44 horas (2640 minutos)'
            })
        
        # Valida cap de horas extras diárias (máximo 2h conforme CLT)
        if data.get('extra_diaria_cap', 0) > 120:  # 2 horas em minutos
            raise serializers.ValidationError({
                'extra_diaria_cap': 'Horas extras diárias não podem exceder 2 horas (120 minutos)'
            })
        
        # Valida período de vigência
        vigencia_inicio = data.get('vigencia_inicio')
        vigencia_fim = data.get('vigencia_fim')
        
        if vigencia_fim and vigencia_inicio and vigencia_fim <= vigencia_inicio:
            raise serializers.ValidationError({
                'vigencia_fim': 'Data fim deve ser posterior à data início'
            })
        
        return data
    
    def validate_banco_horas_prazo_meses(self, value):
        """Valida prazo do banco de horas (máximo 12 meses conforme CLT)"""
        if value > 12:
            raise serializers.ValidationError(
                "Prazo do banco de horas não pode exceder 12 meses"
            )
        return value


class EscalaSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Escala com validações trabalhistas"""
    
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    duracao_minutos = serializers.ReadOnlyField()
    validacoes = serializers.SerializerMethodField()
    
    class Meta:
        model = Escala
        fields = [
            'id', 'funcionario', 'funcionario_nome', 'data', 'hora_inicio',
            'hora_fim', 'pausa_minutos', 'tipo_escala', 'descanso',
            'duracao_minutos', 'validacoes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_validacoes(self, obj):
        """Executa validações trabalhistas para a escala"""
        if obj.descanso:
            return {'valido': True, 'tipo': 'descanso'}
        
        validador = ValidadorRegrasTrabalho()
        
        validacoes = {
            'jornada_diaria': validador.validar_jornada_diaria(obj.funcionario, obj.data),
            'pausa_intrajornada': validador.validar_pausa_intrajornada(obj),
            'interjornada': validador.validar_interjornada(obj.funcionario, obj.data)
        }
        
        # Validações específicas por tipo de escala
        if obj.tipo_escala == '12x36':
            validacoes['escala_12x36'] = validador.validar_escala_12x36(obj)
        
        # Determina se todas as validações passaram
        todas_validas = all(v.get('valido', False) for v in validacoes.values())
        
        return {
            'valido': todas_validas,
            'detalhes': validacoes
        }
    
    def validate(self, data):
        """Validações gerais da escala"""
        if data.get('descanso'):
            # Escalas de descanso não precisam de horários
            return data
        
        hora_inicio = data.get('hora_inicio')
        hora_fim = data.get('hora_fim')
        
        if not hora_inicio or not hora_fim:
            raise serializers.ValidationError(
                "Hora início e fim são obrigatórias para escalas de trabalho"
            )
        
        # Valida se hora fim é posterior à hora início
        if hora_fim <= hora_inicio:
            raise serializers.ValidationError({
                'hora_fim': 'Hora fim deve ser posterior à hora início'
            })
        
        # Calcula duração da jornada
        inicio_dt = datetime.combine(date.today(), hora_inicio)
        fim_dt = datetime.combine(date.today(), hora_fim)
        
        # Se passou da meia-noite
        if hora_fim < hora_inicio:
            fim_dt += timedelta(days=1)
        
        duracao_minutos = int((fim_dt - inicio_dt).total_seconds() / 60)
        
        # Valida duração máxima (12h conforme CLT)
        if duracao_minutos > 720:
            raise serializers.ValidationError(
                "Jornada não pode exceder 12 horas (720 minutos)"
            )
        
        # Valida pausa mínima conforme duração
        pausa_minutos = data.get('pausa_minutos', 0)
        
        if duracao_minutos >= 360:  # >= 6h
            if pausa_minutos < 60:
                raise serializers.ValidationError({
                    'pausa_minutos': 'Jornada >= 6h requer pausa mínima de 60 minutos'
                })
        elif duracao_minutos >= 240:  # >= 4h
            if pausa_minutos < 15:
                raise serializers.ValidationError({
                    'pausa_minutos': 'Jornada >= 4h requer pausa mínima de 15 minutos'
                })
        
        return data
    
    def validate_tipo_escala(self, value):
        """Valida se o funcionário pode usar o tipo de escala"""
        funcionario = self.initial_data.get('funcionario')
        if not funcionario:
            return value
        
        if value == '12x36':
            # Verifica se o contrato permite escala 12x36
            contrato = Contrato.objects.filter(
                funcionario_id=funcionario,
                vigencia_inicio__lte=date.today()
            ).order_by('-vigencia_inicio').first()
            
            if not contrato or not contrato.permite_12x36:
                raise serializers.ValidationError(
                    "Funcionário não autorizado para escala 12x36"
                )
        
        return value


class PontoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Ponto com validações automáticas"""
    
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    escala_data = serializers.DateField(source='escala.data', read_only=True)
    validacoes = serializers.SerializerMethodField()
    
    class Meta:
        model = Ponto
        fields = [
            'id', 'funcionario', 'funcionario_nome', 'escala', 'escala_data',
            'timestamp', 'tipo_registro', 'localizacao_lat', 'localizacao_lng',
            'validado', 'observacoes', 'validacoes', 'created_at'
        ]
        read_only_fields = ['id', 'escala', 'validado', 'created_at']
    
    def get_validacoes(self, obj):
        """Retorna validações do registro de ponto"""
        processador = ProcessadorPontos()
        return processador._validar_registro_ponto(
            obj.funcionario, obj.tipo_registro, obj.timestamp, obj.escala
        )
    
    def create(self, validated_data):
        """Cria registro de ponto com validações automáticas"""
        funcionario = validated_data['funcionario']
        timestamp = validated_data['timestamp']
        tipo_registro = validated_data['tipo_registro']
        
        # Busca escala do dia
        escala = Escala.objects.filter(
            funcionario=funcionario,
            data=timestamp.date()
        ).first()
        
        validated_data['escala'] = escala
        
        # Usa o processador para criar com validações
        processador = ProcessadorPontos()
        localizacao = None
        
        if validated_data.get('localizacao_lat') and validated_data.get('localizacao_lng'):
            localizacao = (validated_data['localizacao_lat'], validated_data['localizacao_lng'])
        
        resultado = processador.registrar_ponto(
            funcionario=funcionario,
            tipo_registro=tipo_registro,
            timestamp=timestamp,
            localizacao=localizacao,
            observacoes=validated_data.get('observacoes', '')
        )
        
        if not resultado['sucesso']:
            raise serializers.ValidationError(resultado.get('erro', 'Erro ao registrar ponto'))
        
        return Ponto.objects.get(id=resultado['ponto_id'])
    
    def validate_timestamp(self, value):
        """Valida timestamp do ponto"""
        # Não permite registros futuros (com tolerância de 5 minutos)
        agora = timezone.now()
        if value > agora + timedelta(minutes=5):
            raise serializers.ValidationError("Não é possível registrar pontos futuros")
        
        # Não permite registros muito antigos (mais de 30 dias)
        limite_passado = agora - timedelta(days=30)
        if value < limite_passado:
            raise serializers.ValidationError("Não é possível registrar pontos com mais de 30 dias")
        
        return value


class BancoHorasSerializer(serializers.ModelSerializer):
    """Serializer para o modelo BancoHoras"""
    
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    saldo_minutos = serializers.ReadOnlyField()
    vencido = serializers.SerializerMethodField()
    
    class Meta:
        model = BancoHoras
        fields = [
            'id', 'funcionario', 'funcionario_nome', 'data_referencia',
            'credito_minutos', 'debito_minutos', 'saldo_minutos',
            'data_vencimento', 'compensado', 'vencido', 'observacoes',
            'created_at'
        ]
        read_only_fields = ['id', 'saldo_minutos', 'data_vencimento', 'created_at']
    
    def get_vencido(self, obj):
        """Verifica se o registro está vencido"""
        return obj.data_vencimento and obj.data_vencimento < date.today()


class SaldoBancoHorasSerializer(serializers.Serializer):
    """Serializer para consulta de saldo do banco de horas"""
    
    funcionario = serializers.PrimaryKeyRelatedField(queryset=Funcionario.objects.all())
    saldo_atual = serializers.IntegerField(read_only=True)
    total_credito = serializers.IntegerField(read_only=True)
    total_debito = serializers.IntegerField(read_only=True)
    registros_vencendo = serializers.IntegerField(read_only=True)
    minutos_vencendo = serializers.IntegerField(read_only=True)


class CompensacaoHorasSerializer(serializers.Serializer):
    """Serializer para compensação de horas do banco"""
    
    funcionario = serializers.PrimaryKeyRelatedField(queryset=Funcionario.objects.all())
    minutos_compensar = serializers.IntegerField(min_value=1)
    data_compensacao = serializers.DateField()
    
    def validate_data_compensacao(self, value):
        """Valida se a data de compensação não é passada"""
        if value < date.today():
            raise serializers.ValidationError("Data de compensação não pode ser passada")
        return value
    
    def create(self, validated_data):
        """Executa a compensação de horas"""
        gerenciador = GerenciadorBancoHoras()
        resultado = gerenciador.compensar_horas(
            funcionario=validated_data['funcionario'],
            minutos_compensar=validated_data['minutos_compensar'],
            data_compensacao=validated_data['data_compensacao']
        )
        
        if not resultado['sucesso']:
            raise serializers.ValidationError(resultado['erro'])
        
        return resultado


class ConfiguracaoSistemaSerializer(serializers.ModelSerializer):
    """Serializer para configurações do sistema"""
    
    class Meta:
        model = ConfiguracaoSistema
        fields = ['id', 'chave', 'valor', 'descricao', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_chave(self, value):
        """Valida se a chave de configuração é válida"""
        chaves_validas = [
            'periodo_noturno_inicio', 'periodo_noturno_fim',
            'interjornada_minima_minutos', 'hora_noturna_urbana_minutos',
            'tolerancia_ponto_minutos', 'dias_limite_edicao_ponto'
        ]
        
        if value not in chaves_validas:
            raise serializers.ValidationError(f"Chave inválida. Válidas: {chaves_validas}")
        
        return value


class EscalaPredefinidaSerializer(serializers.ModelSerializer):
    """Serializer para escalas predefinidas"""
    
    legal = serializers.SerializerMethodField()
    observacoes_legais = serializers.SerializerMethodField()
    
    class Meta:
        model = EscalaPredefinida
        fields = [
            'id', 'nome', 'descricao', 'horas_trabalho', 'horas_descanso',
            'legal', 'observacoes_legais', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_legal(self, obj):
        """Verifica se a escala está em conformidade com a legislação"""
        # Jornada máxima de 12h
        if obj.horas_trabalho > 12:
            return False
        # Interjornada mínima de 11h
        if obj.horas_descanso < 11:
            return False
        return True
    
    def get_observacoes_legais(self, obj):
        """Retorna observações legais sobre a escala"""
        observacoes = {
            '12x36': 'Requer autorização específica no contrato. Folga embutida obrigatória.',
            '6x1': 'Escala comercial padrão. DSR preferencialmente aos domingos.',
            '5x2': 'Escala administrativa. Fins de semana livres.',
            '4x2': 'Escala industrial. Requer pausas adequadas para jornadas longas.'
        }
        return observacoes.get(obj.nome, 'Verificar conformidade com CLT')


class FolgaSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Folga (compatibilidade)"""
    
    funcionario_nome = serializers.CharField(source='funcionario.nome', read_only=True)
    
    class Meta:
        model = Folga
        fields = ['id', 'funcionario', 'funcionario_nome', 'data', 'motivo', 'created_at']
        read_only_fields = ['id', 'created_at']


class RelatorioJornadaSerializer(serializers.Serializer):
    """Serializer para relatórios de jornada"""
    
    funcionario = serializers.PrimaryKeyRelatedField(queryset=Funcionario.objects.all())
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField()
    
    # Campos de resultado
    total_dias = serializers.IntegerField(read_only=True)
    dias_trabalhados = serializers.IntegerField(read_only=True)
    dias_descanso = serializers.IntegerField(read_only=True)
    total_horas_normais = serializers.IntegerField(read_only=True)
    total_horas_extras = serializers.IntegerField(read_only=True)
    total_adicional_noturno = serializers.IntegerField(read_only=True)
    
    def validate(self, data):
        """Valida período do relatório"""
        if data['data_fim'] < data['data_inicio']:
            raise serializers.ValidationError("Data fim deve ser posterior à data início")
        
        # Limita período máximo a 1 ano
        if (data['data_fim'] - data['data_inicio']).days > 365:
            raise serializers.ValidationError("Período máximo de 1 ano")
        
        return data


class ValidacaoEscalaSerializer(serializers.Serializer):
    """Serializer para validação de escalas"""
    
    funcionario = serializers.PrimaryKeyRelatedField(queryset=Funcionario.objects.all())
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField()
    
    # Resultados das validações
    escalas_validas = serializers.ListField(read_only=True)
    escalas_invalidas = serializers.ListField(read_only=True)
    resumo_violacoes = serializers.DictField(read_only=True)
    
    def validate(self, data):
        """Valida período de análise"""
        if data['data_fim'] < data['data_inicio']:
            raise serializers.ValidationError("Data fim deve ser posterior à data início")
        
        return data