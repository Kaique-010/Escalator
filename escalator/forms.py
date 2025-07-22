from django import forms
from .models import Funcionario, Turno, Escala, Folga, EscalaPredefinida

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'matricula', 'cargo', 'ativo']
        labels = {
            'nome': 'Nome completo',
            'matricula': 'Matrícula',
            'cargo': 'Cargo',
            'ativo': 'Ativo',
        }
        help_texts = {
            'matricula': 'Informe a matrícula do funcionário.',
        }

class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = ['nome', 'hora_inicio', 'hora_fim']
        labels = {
            'nome': 'Nome do turno',
            'hora_inicio': 'Hora de início',
            'hora_fim': 'Hora de término',
        }

class EscalaForm(forms.ModelForm):
    class Meta:
        model = Escala
        fields = ['funcionario', 'turno', 'data']
        labels = {
            'funcionario': 'Funcionário',
            'turno': 'Turno',
            'data': 'Data',
        }
        help_texts = {
            'data': 'Selecione a data da escala.',
        }

class FolgaForm(forms.ModelForm):
    class Meta:
        model = Folga
        fields = ['funcionario', 'data', 'motivo']
        labels = {
            'funcionario': 'Funcionário',
            'data': 'Data da folga',
            'motivo': 'Motivo',
        }
        help_texts = {
            'motivo': 'Motivo da folga (opcional).',
        }

class EscalaPredefinidaForm(forms.ModelForm):
    class Meta:
        model = EscalaPredefinida
        fields = ['nome', 'descricao', 'horas_trabalho', 'horas_descanso']
        labels = {
            'nome': 'Nome da escala',
            'descricao': 'Descrição',
            'horas_trabalho': 'Horas de trabalho',
            'horas_descanso': 'Horas de descanso',
        } 