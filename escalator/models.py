from django.db import models
from django.utils.translation import gettext_lazy as _

class Funcionario(models.Model):
    nome = models.CharField(_('Nome'), max_length=100)
    matricula = models.CharField(_('Matrícula'), max_length=20, unique=True)
    cargo = models.CharField(_('Cargo'), max_length=50)
    ativo = models.BooleanField(_('Ativo'), default=True)

    def __str__(self):
        return f"{self.nome} ({self.matricula})"

class Turno(models.Model):
    nome = models.CharField(_('Nome do turno'), max_length=50)
    hora_inicio = models.TimeField(_('Hora de início'))
    hora_fim = models.TimeField(_('Hora de término'))

    def __str__(self):
        return self.nome

class Escala(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name=_('Funcionário'))
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, verbose_name=_('Turno'))
    data = models.DateField(_('Data'))

    class Meta:
        unique_together = ('funcionario', 'data')
        verbose_name = _('Escala')
        verbose_name_plural = _('Escalas')

    def __str__(self):
        return f"{self.funcionario} - {self.turno} em {self.data.strftime('%d/%m/%Y')}"

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

    def __str__(self):
        return f"({self.horas_trabalho}x{self.horas_descanso})"
