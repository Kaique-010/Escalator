from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    # Funcionário
    path('funcionarios/', views.FuncionarioListView.as_view(), name='funcionario-list'),
    path('funcionarios/novo/', views.FuncionarioCreateView.as_view(), name='funcionario-create'),
    path('funcionarios/<int:pk>/editar/', views.FuncionarioUpdateView.as_view(), name='funcionario-update'),
    path('funcionarios/<int:pk>/excluir/', views.FuncionarioDeleteView.as_view(), name='funcionario-delete'),
    path('funcionarios/<int:pk>/', views.FuncionarioDetailView.as_view(), name='funcionario-detail'),

    # Turno
    path('turnos/', views.TurnoListView.as_view(), name='turno-list'),
    path('turnos/novo/', views.TurnoCreateView.as_view(), name='turno-create'),
    path('turnos/<int:pk>/editar/', views.TurnoUpdateView.as_view(), name='turno-update'),
    path('turnos/<int:pk>/excluir/', views.TurnoDeleteView.as_view(), name='turno-delete'),
    path('turnos/<int:pk>/', views.TurnoDetailView.as_view(), name='turno-detail'),

    # Escala
    path('escalas/', views.EscalaListView.as_view(), name='escala-list'),
    path('escalas/novo/', views.EscalaCreateView.as_view(), name='escala-create'),
    path('escalas/<int:pk>/editar/', views.EscalaUpdateView.as_view(), name='escala-update'),
    path('escalas/<int:pk>/excluir/', views.EscalaDeleteView.as_view(), name='escala-delete'),
    path('escalas/<int:pk>/', views.EscalaDetailView.as_view(), name='escala-detail'),
    path('escalas/<int:escala_id>/gerar-folgas/', views.GerarFolgasAutomaticasView.as_view(), name='gerar-folgas-automaticas'),

    # Folga
    path('folgas/', views.FolgaListView.as_view(), name='folga-list'),
    path('folgas/novo/', views.FolgaCreateView.as_view(), name='folga-create'),
    path('folgas/<int:pk>/editar/', views.FolgaUpdateView.as_view(), name='folga-update'),
    path('folgas/<int:pk>/excluir/', views.FolgaDeleteView.as_view(), name='folga-delete'),
    path('folgas/<int:pk>/', views.FolgaDetailView.as_view(), name='folga-detail'),

    # Escalas pré-definidas
    path('escalas-predefinidas/', views.EscalaPredefinidaListView.as_view(), name='escalapredefinida-list'),
    path('escalas-predefinidas/novo/', views.EscalaPredefinidaCreateView.as_view(), name='escalapredefinida-create'),
    path('escalas-predefinidas/<int:pk>/editar/', views.EscalaPredefinidaUpdateView.as_view(), name='escalapredefinida-update'),
    path('escalas-predefinidas/<int:pk>/excluir/', views.EscalaPredefinidaDeleteView.as_view(), name='escalapredefinida-delete'),
    path('escalas-predefinidas/<int:pk>/', views.EscalaPredefinidaDetailView.as_view(), name='escalapredefinida-detail'),
] 