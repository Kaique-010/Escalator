"""
Sistema de autenticação personalizado para multiempresa
"""
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import connections
from .models import Empresa, Licenca
from .routers import create_empresa_database, get_empresa_database, set_db_for_request
from .middleware import EmpresaSessionMiddleware
import logging
from .routers import get_db_for_request

User = get_user_model()
logger = logging.getLogger(__name__)

class MultiEmpresaAuthBackend(ModelBackend):
    """
    Backend de autenticação que suporta múltiplas empresas
    """
    
    def authenticate(self, request, username=None, password=None, empresa_id=None, **kwargs):
        """
        Autentica usuário considerando a empresa
        """
        if username is None or password is None:
            return None
        
        # Logs de debug do fluxo de autenticação
        try:
            logger.info("[AUTH] authenticate inicio | username=%s | has_password=%s | empresa_id=%s | db=%s | path=%s",
                        username, bool(password), empresa_id, get_db_for_request(), getattr(request, 'path', None))
            print("[AUTH] authenticate inicio:", {
                "username": username,
                "has_password": bool(password),
                "empresa_id": empresa_id,
                "db": get_db_for_request(),
                "path": getattr(request, 'path', None)
            })
        except Exception as e:
            print("[WARN] Falha ao coletar debug em authenticate:", str(e))
        
        try:
            # Busca o usuário
            user = User.objects.get(username=username)
            
            # Verifica a senha
            if user.check_password(password):
                # Se empresa_id foi fornecida, verifica se o usuário pertence a ela
                if empresa_id and user.empresa_id != empresa_id:
                    print("[AUTH] empresa mismatch:", {"user_empresa": user.empresa_id, "empresa_id": empresa_id})
                    return None
                
                # Verifica se a empresa está ativa e tem licença válida
                if user.empresa_id:
                    if not self._verificar_empresa_ativa(user.empresa_id):
                        print("[AUTH] empresa inativa ou sem licença:", {"empresa_id": user.empresa_id})
                        return None
                
                try:
                    print("[AUTH] authenticate sucesso:", {"user_id": user.id, "username": user.username})
                except Exception:
                    pass
                
                return user
            else:
                print("[AUTH] senha inválida para usuário:", username)
                
                return None
        except User.DoesNotExist:
            print("[AUTH] usuário não encontrado:", username)
            return None
        
        return None

    def _verificar_empresa_ativa(self, empresa_id):
        """
        Verifica se a empresa está ativa e tem licença válida
        """
        try:
            # Busca no banco master
            empresa = Empresa.objects.using('master').get(id=empresa_id)
            if not empresa.ativa:
                return False
            
            # Verifica se tem licença ativa
            licenca_ativa = Licenca.objects.using('master').filter(
                empresa=empresa,
                status='ativa'
            ).first()
            
            return licenca_ativa is not None and licenca_ativa.is_ativa()
        except Empresa.DoesNotExist:
            return False


def login_multiempresa(request, username, password, empresa_id=None):
    """
    Função de login personalizada para sistema multiempresa
    """
    # Autentica o usuário
    user = authenticate(
        request=request,
        username=username,
        password=password,
        empresa_id=empresa_id
    )
    
    if user is not None:
        # Faz o login
        django_login(request, user)
        
        # Define a empresa na sessão
        if user.empresa_id:
            middleware = EmpresaSessionMiddleware()
            middleware.set_empresa_session(request, user.empresa_id)
            
            # Garante que o banco da empresa existe
            db_alias = get_empresa_database(user.empresa_id)
            if db_alias not in connections.databases:
                create_empresa_database(user.empresa_id)
        
        return user
    
    return None


def logout_multiempresa(request):
    """
    Função de logout personalizada
    """
    # Limpa a empresa da sessão
    middleware = EmpresaSessionMiddleware()
    middleware.clear_empresa_session(request)
    
    # Limpa o banco da thread local
    set_db_for_request(None)
    
    # Faz o logout
    django_logout(request)


def get_empresa_info(user):
    """
    Obtém informações da empresa do usuário
    """
    if not user.empresa_id:
        return None
    
    try:
        empresa = Empresa.objects.using('master').get(id=user.empresa_id)
        licenca = Licenca.objects.using('master').filter(
            empresa=empresa,
            status='ativa'
        ).first()
        
        return {
            'empresa': empresa,
            'licenca': licenca,
            'database_alias': get_empresa_database(user.empresa_id)
        }
    except Empresa.DoesNotExist:
        return None


def verificar_permissoes_empresa(user, acao):
    """
    Verifica se o usuário tem permissão para realizar uma ação baseado na licença
    """
    empresa_info = get_empresa_info(user)
    if not empresa_info or not empresa_info['licenca']:
        return False
    
    licenca = empresa_info['licenca']
    
    # Mapeamento de ações para permissões da licença
    permissoes_map = {
        'banco_horas': licenca.permite_banco_horas,
        'ponto_eletronico': licenca.permite_ponto_eletronico,
        'relatorios_avancados': licenca.permite_relatorios_avancados,
        'integracao_api': licenca.permite_integracao_api,
    }
    
    return permissoes_map.get(acao, False)


def criar_usuario_empresa(username, email, password, first_name, last_name, empresa_id):
    """
    Cria um usuário associado a uma empresa
    """
    try:
        # Verifica se a empresa existe
        empresa = Empresa.objects.using('master').get(id=empresa_id)
        
        # Verifica limites da licença
        licenca = Licenca.objects.using('master').filter(
            empresa=empresa,
            status='ativa'
        ).first()
        
        if not licenca:
            raise ValueError("Empresa não possui licença ativa")
        
        # Conta usuários existentes da empresa
        usuarios_existentes = User.objects.filter(empresa_id=empresa_id).count()
        if usuarios_existentes >= licenca.max_usuarios:
            raise ValueError(f"Limite de usuários atingido ({licenca.max_usuarios})")
        
        # Cria o usuário
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            empresa_id=empresa_id
        )
        
        return user
        
    except Empresa.DoesNotExist:
        raise ValueError("Empresa não encontrada")