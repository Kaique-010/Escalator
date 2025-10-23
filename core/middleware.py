"""
Middleware para roteamento de banco de dados baseado na empresa
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.db import connections
from .routers import set_db_for_request, get_empresa_database, create_empresa_database
from .routers import get_db_for_request
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class DatabaseRoutingMiddleware(MiddlewareMixin):
    """
    Middleware que define o banco de dados a ser usado baseado na empresa do usuário
    """
    
    def process_request(self, request):
        """
        Processa a requisição e define o banco de dados apropriado
        """
        # Log inicial da requisição para rastrear roteamento
        try:
            logger.info("[ROUTER] request path=%s | authenticated=%s | method=%s", getattr(request, 'path', None), getattr(getattr(request, 'user', None), 'is_authenticated', False), getattr(request, 'method', None))
            print("[ROUTER] início:", {"path": getattr(request, 'path', None), "authenticated": getattr(getattr(request, 'user', None), 'is_authenticated', False), "method": getattr(request, 'method', None)})
        except Exception:
            pass
        # Se o usuário está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Tenta obter a empresa do usuário
                empresa_id = self.get_empresa_from_user(request.user)
                
                if empresa_id:
                    # Define o banco da empresa
                    db_alias = get_empresa_database(empresa_id)
                    
                    # Verifica se o banco existe, se não, cria
                    if db_alias not in connections.databases:
                        create_empresa_database(empresa_id)
                    
                    # Define o banco para a requisição
                    set_db_for_request(db_alias)
                    print("[ROUTER] autenticado com empresa:", {"empresa_id": empresa_id, "db_alias": db_alias})
                else:
                    # Se não tem empresa, usa o banco default
                    set_db_for_request('default')
                    print("[ROUTER] autenticado sem empresa, usando default")
                    
            except Exception as e:
                # Em caso de erro, usa o banco default
                set_db_for_request('default')
                print("[ROUTER] erro ao definir banco, fallback default:", str(e))
        else:
            # Usuário não autenticado, usa banco default
            set_db_for_request('default')
            print("[ROUTER] não autenticado, usando default")
        try:
            print("[ROUTER] banco atual:", get_db_for_request())
        except Exception:
            pass
     
    def get_empresa_from_user(self, user):
        """
        Obtém o ID da empresa do usuário
        Pode ser implementado de diferentes formas dependendo da estrutura
        """
        # Opção 1: Se o usuário tem um campo empresa diretamente
        if hasattr(user, 'empresa_id') and user.empresa_id:
            return user.empresa_id
        
        # Opção 2: Se há uma relação através de funcionário
        if hasattr(user, 'funcionario'):
            funcionario = user.funcionario
            if hasattr(funcionario, 'empresa_id'):
                return funcionario.empresa_id
        
        # Opção 3: Buscar na sessão (definido no login)
        # Esta será a implementação principal para casos especiais
        return None
    
    def process_response(self, request, response):
        """
        Limpa as configurações de banco após a resposta
        """
        # Limpa a configuração do thread local
        set_db_for_request(None)
        return response


class EmpresaSessionMiddleware(MiddlewareMixin):
    """
    Middleware adicional para gerenciar a empresa na sessão
    """
    
    def process_request(self, request):
        """
        Verifica se há uma empresa definida na sessão
        """
        if hasattr(request, 'session'):
            empresa_id = request.session.get('empresa_id')
            if empresa_id:
                # Define o banco baseado na empresa da sessão
                db_alias = get_empresa_database(empresa_id)
                
                # Verifica se o banco existe
                if db_alias not in connections.databases:
                    create_empresa_database(empresa_id)
                
                set_db_for_request(db_alias)
                print("[ROUTER] sessão empresa ativa:", {"empresa_id": empresa_id, "db_alias": db_alias})
    
    def set_empresa_session(self, request, empresa_id):
        """
        Define a empresa na sessão
        """
        request.session['empresa_id'] = empresa_id
        request.session.save()
    
    def clear_empresa_session(self, request):
        """
        Remove a empresa da sessão
        """
        if 'empresa_id' in request.session:
            del request.session['empresa_id']
            request.session.save()