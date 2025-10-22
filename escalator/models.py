import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta

User = get_user_model()

class Funcionario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('Usuário'), null=True, blank=True)
    nome = models.CharField(_('Nome'), max_length=100)
    matricula = models.CharField(_('Matrícula'), max_length=20, unique=True)
    cargo = models.CharField(_('Cargo'), max_length=50)
    ativo = models.BooleanField(_('Ativo'), default=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Funcionário')
        verbose_name_plural = _('Funcionários')

    def __str__(self):
        return f"{self.nome} ({self.matricula})"

class Turno(models.Model):
    nome = models.CharField(_('Nome do turno'), max_length=50)
    hora_inicio = models.TimeField(_('Hora de início'))
    hora_fim = models.TimeField(_('Hora de término'))

    def __str__(self):
        return self.nome

class Escala(models.Model):
    TIPO_ESCALA_CHOICES = [
        ('normal', _('Normal')),
        ('12x36', _('12x36')),
        ('noturna', _('Noturna')),
        ('extra', _('Hora Extra')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name=_('Funcionário'))
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, verbose_name=_('Turno'), null=True, blank=True)
    data = models.DateField(_('Data'))
    hora_inicio = models.TimeField(_('Hora de início'), null=True, blank=True)
    hora_fim = models.TimeField(_('Hora de término'), null=True, blank=True)
    pausa_minutos = models.PositiveIntegerField(_('Pausa em minutos'), default=60)
    tipo_escala = models.CharField(_('Tipo de escala'), max_length=20, choices=TIPO_ESCALA_CHOICES, default='normal')
    descanso = models.BooleanField(_('Dia de descanso (DSR)'), default=False)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        unique_together = ('funcionario', 'data')
        verbose_name = _('Escala')
        verbose_name_plural = _('Escalas')
        ordering = ['-data']

    def __str__(self):
        if self.descanso:
            return f"{self.funcionario} - DSR em {self.data.strftime('%d/%m/%Y')}"
        return f"{self.funcionario} - {self.tipo_escala} em {self.data.strftime('%d/%m/%Y')}"

    @property
    def duracao_minutos(self):
        """Calcula a duração da jornada em minutos"""
        if self.descanso or not self.hora_inicio or not self.hora_fim:
            return 0
        
        inicio = datetime.combine(self.data, self.hora_inicio)
        fim = datetime.combine(self.data, self.hora_fim)
        
        # Se hora fim é menor que início, passou da meia-noite
        if self.hora_fim < self.hora_inicio:
            fim += timedelta(days=1)
        
        duracao = fim - inicio
        return int(duracao.total_seconds() / 60) - self.pausa_minutos

class Folga(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name=_('Funcionário'))
    data = models.DateField(_('Data da folga'))
    motivo = models.CharField(_('Motivo'), max_length=100, blank=True)

    class Meta:
        unique_together = ('funcionario', 'data')
        verbose_name = _('Folga')
        verbose_name_plural = _('Folgas')

    def __str__(self):
        return f"{self.funcionario} - {self.data.strftime('%d/%m/%Y')}"

class EscalaPredefinida(models.Model):
    nome = models.CharField('Nome da escala', max_length=50, unique=True)
    descricao = models.CharField('Descrição', max_length=100, blank=True)
    horas_trabalho = models.PositiveIntegerField('Horas de trabalho')
    horas_descanso = models.PositiveIntegerField('Horas de descanso')

    class Meta:
        verbose_name = _('Escala Predefinida')
        verbose_name_plural = _('Escalas Predefinidas')

    def __str__(self):
        return f"{self.nome} ({self.horas_trabalho}x{self.horas_descanso})"

class Contrato(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name=_('Funcionário'))
    carga_diaria_max = models.PositiveIntegerField(_('Carga diária máxima (minutos)'), default=480)
    carga_semanal_max = models.PositiveIntegerField(_('Carga semanal máxima (minutos)'), default=2640)
    extra_diaria_cap = models.PositiveIntegerField(_('Limite diário de horas extras (minutos)'), default=120)
    banco_horas_prazo_meses = models.PositiveIntegerField(_('Prazo banco de horas (meses)'), default=12)
    permite_12x36 = models.BooleanField(_('Permite escala 12x36'), default=False)
    vigencia_inicio = models.DateField(_('Vigência início'))
    vigencia_fim = models.DateField(_('Vigência fim'), null=True, blank=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Contrato')
        verbose_name_plural = _('Contratos')
        ordering = ['-vigencia_inicio']

    def __str__(self):
        return f"Contrato {self.funcionario.nome} - {self.vigencia_inicio}"

    def is_vigente(self, data=None):
        """Verifica se o contrato está vigente na data especificada"""
        if data is None:
            data = datetime.now().date()
        
        if data < self.vigencia_inicio:
            return False
        
        if self.vigencia_fim and data > self.vigencia_fim:
            return False
        
        return True

class Ponto(models.Model):
    TIPO_REGISTRO_CHOICES = [
        ('entrada', _('Entrada')),
        ('saida', _('Saída')),
        ('pausa_inicio', _('Início da Pausa')),
        ('pausa_fim', _('Fim da Pausa')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name=_('Funcionário'))
    escala = models.ForeignKey(Escala, on_delete=models.CASCADE, verbose_name=_('Escala'), null=True, blank=True)
    timestamp = models.DateTimeField(_('Data e hora'))
    tipo_registro = models.CharField(_('Tipo de registro'), max_length=20, choices=TIPO_REGISTRO_CHOICES)
    localizacao_lat = models.FloatField(_('Latitude'), null=True, blank=True)
    localizacao_lng = models.FloatField(_('Longitude'), null=True, blank=True)
    validado = models.BooleanField(_('Validado'), default=False)
    observacoes = models.TextField(_('Observações'), blank=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Ponto')
        verbose_name_plural = _('Pontos')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.funcionario.nome} - {self.get_tipo_registro_display()} em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

class BancoHoras(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name=_('Funcionário'))
    data_referencia = models.DateField(_('Data de referência'))
    credito_minutos = models.IntegerField(_('Crédito (minutos)'), default=0)
    debito_minutos = models.IntegerField(_('Débito (minutos)'), default=0)
    saldo_minutos = models.IntegerField(_('Saldo (minutos)'), default=0)
    data_vencimento = models.DateField(_('Data de vencimento'), null=True, blank=True)
    compensado = models.BooleanField(_('Compensado'), default=False)
    observacoes = models.TextField(_('Observações'), blank=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Banco de Horas')
        verbose_name_plural = _('Banco de Horas')
        unique_together = ('funcionario', 'data_referencia')
        ordering = ['-data_referencia']

    def __str__(self):
        return f"{self.funcionario.nome} - {self.data_referencia.strftime('%d/%m/%Y')} - Saldo: {self.saldo_minutos}min"

    def save(self, *args, **kwargs):
        # Calcula o saldo automaticamente
        self.saldo_minutos = self.credito_minutos - self.debito_minutos
        
        # Define data de vencimento se não foi definida
        if not self.data_vencimento and self.funcionario:
            try:
                contrato = Contrato.objects.filter(
                    funcionario=self.funcionario,
                    vigencia_inicio__lte=self.data_referencia
                ).order_by('-vigencia_inicio').first()
                
                if contrato:
                    self.data_vencimento = self.data_referencia + relativedelta(months=contrato.banco_horas_prazo_meses)
            except:
                # Se não encontrar contrato, usa 12 meses como padrão
                self.data_vencimento = self.data_referencia + relativedelta(months=12)
        
        super().save(*args, **kwargs)

class ConfiguracaoSistema(models.Model):
    chave = models.CharField(_('Chave'), max_length=100, unique=True)
    valor = models.CharField(_('Valor'), max_length=200)
    descricao = models.TextField(_('Descrição'), blank=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Configuração do Sistema')
        verbose_name_plural = _('Configurações do Sistema')

    def __str__(self):
        return f"{self.chave}: {self.valor}"

    @classmethod
    def get_valor(cls, chave, default=None):
        """Método utilitário para obter valor de configuração"""
        try:
            config = cls.objects.get(chave=chave)
            return config.valor
        except cls.DoesNotExist:
            return default

    @classmethod
    def get_periodo_noturno(cls):
        """Retorna o período noturno configurado"""
        inicio = cls.get_valor('periodo_noturno_inicio', '22:00')
        fim = cls.get_valor('periodo_noturno_fim', '05:00')
        return time.fromisoformat(inicio), time.fromisoformat(fim)

    @classmethod
    def get_interjornada_minima(cls):
        """Retorna o intervalo mínimo entre jornadas em minutos"""
        return int(cls.get_valor('interjornada_minima_minutos', '660'))
