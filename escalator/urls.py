"""
URLs para o sistema de gerenciamento de escalas.
Configura rotas para APIs REST e views tradicionais.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Logs de depuração do fluxo de login
        try:
            from core.routers import get_db_for_request
            print("=== DEBUG /api/token/ POST ===")
            print("Path:", getattr(request, 'path', None))
            print("Headers Authorization:", request.headers.get("Authorization"))
            print("Body keys:", list(getattr(request, 'data', {}).keys()))
            print("DB alias atual:", get_db_for_request())
        except Exception as e:
            print("[WARN] Falha ao coletar debug do login:", str(e))
        
        response = super().post(request, *args, **kwargs)
        
        try:
            print("Status:", getattr(response, 'status_code', None))
            # Evitar logar tokens, apenas estado
            print("=== FIM DEBUG /api/token/ ===")
        except Exception:
            pass
        
        return response

# Router para APIs REST
router = DefaultRouter()
router.register(r'api/funcionarios', views.FuncionarioViewSet)
router.register(r'api/contratos', views.ContratoViewSet)
router.register(r'api/escalas', views.EscalaViewSet)
router.register(r'api/pontos', views.PontoViewSet)
router.register(r'api/banco-horas', views.BancoHorasViewSet)
router.register(r'api/configuracoes', views.ConfiguracaoSistemaViewSet)
router.register(r'api/escalas-predefinidas', views.EscalaPredefinidaViewSet)
router.register(r'api/folgas', views.FolgaViewSet)
router.register(r'api/relatorios', views.RelatoriosViewSet, basename='relatorios')

urlpatterns = [
    # APIs REST
    path('', include(router.urls)),
    
    # Endpoints para autenticação JWT
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]