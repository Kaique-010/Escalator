"""
Admin para os modelos do core (Empresa e Licença)
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Empresa, Licenca, LicencaHistorico

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'razao_social', 'cnpj', 'email', 
        'cidade', 'estado', 'ativa', 'created_at'
    ]
    list_filter = ['ativa', 'estado', 'created_at']
    search_fields = ['nome', 'razao_social', 'cnpj', 'email']
    readonly_fields = ['uuid', 'database_name', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'razao_social', 'cnpj', 'email', 'telefone')
        }),
        ('Endereço', {
            'fields': ('endereco', 'cidade', 'estado', 'cep')
        }),
        ('Sistema', {
            'fields': ('uuid', 'database_name', 'ativa')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).using('master')


class LicencaHistoricoInline(admin.TabularInline):
    model = LicencaHistorico
    extra = 0
    readonly_fields = ['acao', 'detalhes', 'usuario', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Licenca)
class LicencaAdmin(admin.ModelAdmin):
    list_display = [
        'empresa', 'tipo', 'status', 'max_funcionarios', 
        'data_inicio', 'data_fim', 'dias_restantes_display', 'valor_mensal'
    ]
    list_filter = ['tipo', 'status', 'data_inicio', 'permite_banco_horas']
    search_fields = ['empresa__nome', 'empresa__cnpj']
    readonly_fields = ['created_at', 'updated_at', 'dias_restantes_display']
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Licença', {
            'fields': ('tipo', 'status', 'data_inicio', 'data_fim', 'valor_mensal')
        }),
        ('Limites', {
            'fields': ('max_funcionarios', 'max_usuarios')
        }),
        ('Funcionalidades', {
            'fields': (
                'permite_banco_horas', 'permite_ponto_eletronico',
                'permite_relatorios_avancados', 'permite_integracao_api'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [LicencaHistoricoInline]
    
    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes()
        if dias is None:
            return "Sem limite"
        elif dias <= 0:
            return format_html('<span style="color: red;">Expirada</span>')
        elif dias <= 30:
            return format_html('<span style="color: orange;">{} dias</span>', dias)
        else:
            return f"{dias} dias"
    
    dias_restantes_display.short_description = 'Dias Restantes'
    
    def get_queryset(self, request):
        return super().get_queryset(request).using('master')


@admin.register(LicencaHistorico)
class LicencaHistoricoAdmin(admin.ModelAdmin):
    list_display = ['licenca', 'acao', 'usuario', 'created_at']
    list_filter = ['acao', 'created_at']
    search_fields = ['licenca__empresa__nome', 'acao', 'usuario']
    readonly_fields = ['licenca', 'acao', 'detalhes', 'usuario', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).using('master')