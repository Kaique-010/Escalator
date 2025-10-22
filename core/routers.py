"""
Roteador de banco de dados para sistema multiempresa
"""
import threading
from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured

# Thread local para armazenar o banco atual da requisição
_thread_local = threading.local()

class DatabaseRouter:
    """
    Roteador que direciona as operações de banco de dados baseado na empresa do usuário
    """
    
    def db_for_read(self, model, **hints):
        """Determina qual banco usar para leitura"""
        # Modelos que sempre vão para o banco master
        if self._is_master_model(model):
            return 'master'
        
        # Pega o banco da thread local (definido pelo middleware)
        db_alias = getattr(_thread_local, 'db_alias', None)
        if db_alias:
            return db_alias
        
        # Fallback para default se não houver definição
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Determina qual banco usar para escrita"""
        # Modelos que sempre vão para o banco master
        if self._is_master_model(model):
            return 'master'
        
        # Pega o banco da thread local (definido pelo middleware)
        db_alias = getattr(_thread_local, 'db_alias', None)
        if db_alias:
            return db_alias
        
        # Fallback para default se não houver definição
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Permite relações apenas entre objetos do mesmo banco"""
        db_set = {'default', 'master'}
        
        # Adiciona todos os bancos de empresa configurados
        for db_alias in connections:
            if db_alias.startswith('empresa_'):
                db_set.add(db_alias)
        
        # Permite relações se ambos objetos estão no mesmo banco
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return obj1._state.db == obj2._state.db
        
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Controla quais migrações podem ser executadas em cada banco"""
        
        # Banco master: apenas modelos de empresa e licença
        if db == 'master':
            return app_label == 'core' and model_name in ['empresa', 'licenca']
        
        # Bancos de empresa: todos os modelos exceto empresa e licença
        if db.startswith('empresa_'):
            if app_label == 'core' and model_name in ['empresa', 'licenca']:
                return False
            return True
        
        # Banco default: desenvolvimento e fallback
        if db == 'default':
            return True
        
        return None
    
    def _is_master_model(self, model):
        """Verifica se o modelo deve sempre usar o banco master"""
        master_models = ['Empresa', 'Licenca']
        return model.__name__ in master_models


def set_db_for_request(db_alias):
    """Define o banco de dados para a requisição atual"""
    _thread_local.db_alias = db_alias


def get_db_for_request():
    """Obtém o banco de dados da requisição atual"""
    return getattr(_thread_local, 'db_alias', 'default')


def create_empresa_database(empresa_id):
    """
    Cria dinamicamente um banco de dados para uma empresa
    """
    db_alias = f'empresa_{empresa_id}'
    
    # Adiciona a configuração do banco dinamicamente
    if db_alias not in settings.DATABASES:
        # Copia a configuração base do banco default
        default_config = settings.DATABASES['default'].copy()
        default_config['NAME'] = str(settings.BASE_DIR / 'databases' / f'{db_alias}.sqlite3')
        
        settings.DATABASES[db_alias] = default_config
    
    # Força a reconexão para garantir que o novo banco seja reconhecido
    if db_alias in connections:
        connections[db_alias].close()
    
    return db_alias


def get_empresa_database(empresa_id):
    """
    Retorna o alias do banco de dados de uma empresa
    """
    return f'empresa_{empresa_id}'