"""
Modelos para o banco principal (master)
Contém informações de empresas e licenças
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from datetime import datetime, timedelta
import uuid

class Empresa(models.Model):
    """
    Modelo para armazenar informações das empresas
    Fica no banco master
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nome = models.CharField(_('Nome da Empresa'), max_length=200)
    razao_social = models.CharField(_('Razão Social'), max_length=200)
    
    # Validador para CNPJ
    cnpj_validator = RegexValidator(
        regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
        message='CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX'
    )
    cnpj = models.CharField(
        _('CNPJ'), 
        max_length=18, 
        unique=True,
        validators=[cnpj_validator]
    )
    
    email = models.EmailField(_('Email'), max_length=200)
    telefone = models.CharField(_('Telefone'), max_length=20, blank=True)
    
    # Endereço
    endereco = models.CharField(_('Endereço'), max_length=300, blank=True)
    cidade = models.CharField(_('Cidade'), max_length=100, blank=True)
    estado = models.CharField(_('Estado'), max_length=2, blank=True)
    cep = models.CharField(_('CEP'), max_length=10, blank=True)
    
    # Status
    ativa = models.BooleanField(_('Ativa'), default=True)
    
    # Configurações de banco
    database_name = models.CharField(
        _('Nome do Banco de Dados'), 
        max_length=100, 
        blank=True,
        help_text='Nome do banco de dados específico da empresa'
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Empresa')
        verbose_name_plural = _('Empresas')
        ordering = ['nome']
        db_table = 'empresa'
    
    def __str__(self):
        return f"{self.nome} ({self.cnpj})"
    
    def save(self, *args, **kwargs):
        # Define o nome do banco automaticamente se não foi definido
        if not self.database_name:
            self.database_name = f'empresa_{self.id or "new"}'
        super().save(*args, **kwargs)
    
    def get_database_alias(self):
        """Retorna o alias do banco de dados da empresa"""
        return f'empresa_{self.id}'


class Licenca(models.Model):
    """
    Modelo para controlar as licenças das empresas
    Fica no banco master
    """
    TIPO_LICENCA_CHOICES = [
        ('trial', _('Trial')),
        ('basica', _('Básica')),
        ('profissional', _('Profissional')),
        ('enterprise', _('Enterprise')),
    ]
    
    STATUS_CHOICES = [
        ('ativa', _('Ativa')),
        ('suspensa', _('Suspensa')),
        ('expirada', _('Expirada')),
        ('cancelada', _('Cancelada')),
    ]
    
    id = models.BigAutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        verbose_name=_('Empresa'),
        related_name='licencas'
    )
    
    tipo = models.CharField(
        _('Tipo de Licença'), 
        max_length=20, 
        choices=TIPO_LICENCA_CHOICES,
        default='trial'
    )
    
    status = models.CharField(
        _('Status'), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default='ativa'
    )
    
    # Limites da licença
    max_funcionarios = models.PositiveIntegerField(
        _('Máximo de Funcionários'), 
        default=10,
        help_text='Número máximo de funcionários permitidos'
    )
    
    max_usuarios = models.PositiveIntegerField(
        _('Máximo de Usuários'), 
        default=5,
        help_text='Número máximo de usuários do sistema'
    )
    
    # Funcionalidades habilitadas
    permite_banco_horas = models.BooleanField(_('Permite Banco de Horas'), default=True)
    permite_ponto_eletronico = models.BooleanField(_('Permite Ponto Eletrônico'), default=True)
    permite_relatorios_avancados = models.BooleanField(_('Permite Relatórios Avançados'), default=False)
    permite_integracao_api = models.BooleanField(_('Permite Integração API'), default=False)
    
    # Datas
    data_inicio = models.DateField(_('Data de Início'))
    data_fim = models.DateField(_('Data de Fim'), null=True, blank=True)
    
    # Informações de pagamento
    valor_mensal = models.DecimalField(
        _('Valor Mensal'), 
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Licença')
        verbose_name_plural = _('Licenças')
        ordering = ['-created_at']
        db_table = 'licenca'
    
    def __str__(self):
        return f"{self.empresa.nome} - {self.get_tipo_display()} ({self.get_status_display()})"
    
    def is_ativa(self):
        """Verifica se a licença está ativa"""
        if self.status != 'ativa':
            return False
        
        if self.data_fim and self.data_fim < datetime.now().date():
            return False
        
        return True
    
    def dias_restantes(self):
        """Calcula quantos dias restam na licença"""
        if not self.data_fim:
            return None
        
        hoje = datetime.now().date()
        if self.data_fim <= hoje:
            return 0
        
        return (self.data_fim - hoje).days
    
    def save(self, *args, **kwargs):
        # Atualiza o status baseado na data
        if self.data_fim and self.data_fim < datetime.now().date():
            self.status = 'expirada'
        
        super().save(*args, **kwargs)


class LicencaHistorico(models.Model):
    """
    Histórico de alterações nas licenças
    """
    licenca = models.ForeignKey(
        Licenca, 
        on_delete=models.CASCADE, 
        verbose_name=_('Licença'),
        related_name='historico'
    )
    
    acao = models.CharField(_('Ação'), max_length=100)
    detalhes = models.TextField(_('Detalhes'), blank=True)
    usuario = models.CharField(_('Usuário'), max_length=100, blank=True)
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Histórico de Licença')
        verbose_name_plural = _('Histórico de Licenças')
        ordering = ['-created_at']
        db_table = 'licenca_historico'
    
    def __str__(self):
        return f"{self.licenca.empresa.nome} - {self.acao}"


# Signals para criação automática de banco e configuração inicial
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.management import call_command
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Empresa)
def criar_banco_empresa(sender, instance, created, **kwargs):
    """
    Signal que é executado após salvar uma Empresa.
    Se for uma nova empresa (created=True), cria o banco e executa as configurações iniciais.
    """
    if created:
        try:
            logger.info(f"Criando banco para nova empresa: {instance.nome}")
            
            # Atualizar o database_name se necessário
            if not instance.database_name or instance.database_name == 'empresa_new':
                instance.database_name = f'empresa_{instance.id}'
                # Usar update para evitar recursão do signal
                Empresa.objects.filter(id=instance.id).update(database_name=instance.database_name)
            
            # Importar a função de criação de banco
            from .routers import create_empresa_database
            
            # Criar o banco de dados da empresa
            create_empresa_database(instance.id)
            logger.info(f"Banco criado para empresa {instance.nome}")
            
            # Executar migrações no banco da empresa
            database_alias = f'empresa_{instance.id}'
            
            # Migrações essenciais
            apps_to_migrate = [
                'contenttypes',
                'auth', 
                'admin',
                'sessions',
                'usuarios',
                'escalator'  # Executar todas as migrações do escalator
            ]
            
            for app_config in apps_to_migrate:
                call_command('migrate', app_config, database=database_alias, verbosity=0)
                logger.info(f"Migração {app_config} executada para empresa {instance.nome}")
            
            # Executar comando de configuração inicial de dados usando o comando setup_initial_data
            # Usar o parâmetro --database para especificar o banco da empresa
            try:
                call_command('setup_initial_data', database=database_alias, verbosity=0)
                logger.info(f"Dados iniciais configurados para empresa {instance.nome}")
            except Exception as e:
                logger.warning(f"Erro ao configurar dados iniciais para empresa {instance.nome}: {str(e)}")
                # Não falha a criação da empresa se houver erro nos dados iniciais
            
            logger.info(f"Configuração completa da empresa {instance.nome} finalizada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao criar banco para empresa {instance.nome}: {str(e)}")
            # Não re-raise a exceção para não impedir a criação da empresa no master