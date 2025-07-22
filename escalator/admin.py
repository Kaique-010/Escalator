from .models import Funcionario, Turno, Escala, Folga, EscalaPredefinida
from django.contrib import admin

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "cargo", "ativo")
    search_fields = ("nome", "matricula", "cargo")
    list_filter = ("ativo",)

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ("nome", "hora_inicio", "hora_fim")
    search_fields = ("nome",)

@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ("funcionario", "turno", "data")
    list_filter = ("turno", "data")
    search_fields = ("funcionario__nome", "turno__nome")

@admin.register(Folga)
class FolgaAdmin(admin.ModelAdmin):
    list_display = ("funcionario", "data", "motivo")
    list_filter = ("data",)
    search_fields = ("funcionario__nome", "motivo")

@admin.register(EscalaPredefinida)
class EscalaPredefinidaAdmin(admin.ModelAdmin):
    list_display = ("nome", "horas_trabalho", "horas_descanso", "descricao")
    search_fields = ("nome", "descricao")
