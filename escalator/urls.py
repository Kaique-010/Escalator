"""
URLs para o sistema de gerenciamento de escalas.
Configura rotas para APIs REST e views tradicionais.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

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
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]