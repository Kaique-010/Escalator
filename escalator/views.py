from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import EscalaPredefinida, Funcionario, Turno, Escala, Folga
from datetime import date
from .forms import EscalaPredefinidaForm
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Escala, Folga, EscalaPredefinida
from datetime import timedelta

from django.views import View

# Funcionário
class FuncionarioListView(ListView):
    model = Funcionario
    template_name = 'escalator/funcionario_list.html'
    context_object_name = 'funcionarios'

class FuncionarioCreateView(CreateView):
    model = Funcionario
    fields = ['nome', 'matricula', 'cargo', 'ativo']
    template_name = 'escalator/funcionario_form.html'
    success_url = reverse_lazy('funcionario-list')

class FuncionarioUpdateView(UpdateView):
    model = Funcionario
    fields = ['nome', 'matricula', 'cargo', 'ativo']
    template_name = 'escalator/funcionario_form.html'
    success_url = reverse_lazy('funcionario-list')

class FuncionarioDeleteView(DeleteView):
    model = Funcionario
    template_name = 'escalator/funcionario_confirm_delete.html'
    success_url = reverse_lazy('funcionario-list')

class FuncionarioDetailView(DetailView):
    model = Funcionario
    template_name = 'escalator/funcionario_detail.html'

# Turno
class TurnoListView(ListView):
    model = Turno
    template_name = 'escalator/turno_list.html'
    context_object_name = 'turnos'

class TurnoCreateView(CreateView):
    model = Turno
    fields = ['nome', 'hora_inicio', 'hora_fim']
    template_name = 'escalator/turno_form.html'
    success_url = reverse_lazy('turno-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['escalas_predefinidas'] = EscalaPredefinida.objects.all()
        return context

class TurnoUpdateView(UpdateView):
    model = Turno
    fields = ['nome', 'hora_inicio', 'hora_fim']
    template_name = 'escalator/turno_form.html'
    success_url = reverse_lazy('turno-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['escalas_predefinidas'] = EscalaPredefinida.objects.all()
        return context

class TurnoDeleteView(DeleteView):
    model = Turno
    template_name = 'escalator/turno_confirm_delete.html'
    success_url = reverse_lazy('turno-list')

class TurnoDetailView(DetailView):
    model = Turno
    template_name = 'escalator/turno_detail.html'

# Escala
class EscalaListView(ListView):
    model = Escala
    template_name = 'escalator/escala_list.html'
    context_object_name = 'escalas'

class EscalaCreateView(CreateView):
    model = Escala
    fields = ['funcionario', 'turno', 'data']
    template_name = 'escalator/escala_form.html'
    success_url = reverse_lazy('escala-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['escalas_predefinidas'] = EscalaPredefinida.objects.all()
        return context

class EscalaUpdateView(UpdateView):
    model = Escala
    fields = ['funcionario', 'turno', 'data']
    template_name = 'escalator/escala_form.html'
    success_url = reverse_lazy('escala-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['escalas_predefinidas'] = EscalaPredefinida.objects.all()
        return context

class EscalaDeleteView(DeleteView):
    model = Escala
    template_name = 'escalator/escala_confirm_delete.html'
    success_url = reverse_lazy('escala-list')

class EscalaDetailView(DetailView):
    model = Escala
    template_name = 'escalator/escala_detail.html'

# Folga
class FolgaListView(ListView):
    model = Folga
    template_name = 'escalator/folga_list.html'
    context_object_name = 'folgas'

class FolgaCreateView(CreateView):
    model = Folga
    fields = ['funcionario', 'data', 'motivo']
    template_name = 'escalator/folga_form.html'
    success_url = reverse_lazy('folga-list')

class FolgaUpdateView(UpdateView):
    model = Folga
    fields = ['funcionario', 'data', 'motivo']
    template_name = 'escalator/folga_form.html'
    success_url = reverse_lazy('folga-list')

class FolgaDeleteView(DeleteView):
    model = Folga
    template_name = 'escalator/folga_confirm_delete.html'
    success_url = reverse_lazy('folga-list')

class FolgaDetailView(DetailView):
    model = Folga
    template_name = 'escalator/folga_detail.html'

class EscalaPredefinidaListView(ListView):
    model = EscalaPredefinida
    template_name = 'escalator/escalapredefinida_list.html'
    context_object_name = 'escalas_predefinidas'

class EscalaPredefinidaCreateView(CreateView):
    model = EscalaPredefinida
    form_class = EscalaPredefinidaForm
    template_name = 'escalator/escalapredefinida_form.html'
    success_url = reverse_lazy('escalapredefinida-list')

class EscalaPredefinidaUpdateView(UpdateView):
    model = EscalaPredefinida
    form_class = EscalaPredefinidaForm
    template_name = 'escalator/escalapredefinida_form.html'
    success_url = reverse_lazy('escalapredefinida-list')

class EscalaPredefinidaDeleteView(DeleteView):
    model = EscalaPredefinida
    template_name = 'escalator/escalapredefinida_confirm_delete.html'
    success_url = reverse_lazy('escalapredefinida-list')

class EscalaPredefinidaDetailView(DetailView):
    model = EscalaPredefinida
    template_name = 'escalator/escalapredefinida_detail.html'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'escalator/dashboard.html'
    login_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_funcionarios'] = Funcionario.objects.count()
        context['total_turnos'] = Turno.objects.count()
        context['total_escalas'] = Escala.objects.count()
        context['total_folgas'] = Folga.objects.count()
        context['escalas_hoje'] = Escala.objects.filter(data=date.today())
        context['folgas_hoje'] = Folga.objects.filter(data=date.today())
        return context

class GerarFolgasAutomaticasView(View):
    def post(self, request, escala_id):
        escala = get_object_or_404(Escala, pk=escala_id)
        funcionario = escala.funcionario
        # Buscar a escala pré-definida correspondente ao turno
        turno = escala.turno
        # Procurar por uma escala pré-definida compatível
        predef = EscalaPredefinida.objects.filter(horas_trabalho=(turno.hora_fim.hour - turno.hora_inicio.hour) % 24).first()
        if not predef:
            messages.error(request, 'Não foi possível identificar a escala pré-definida para sugerir folgas.')
            return redirect(reverse('escala-detail', args=[escala_id]))
        # Gerar folga após o período de trabalho
        data_folga = escala.data + timedelta(hours=predef.horas_trabalho)
        for i in range(predef.horas_descanso // 24):
            Folga.objects.get_or_create(funcionario=funcionario, data=data_folga + timedelta(days=i))
        messages.success(request, f'Folgas sugeridas automaticamente para {funcionario.nome}!')
        return redirect(reverse('escala-detail', args=[escala_id]))
