from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.LoginView.as_view(), name='login_root'),
    path('registrar/', views.registrar, name='registrar'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('perfil/<int:usuario_id>/', views.PerfilDetailView.as_view(), name='perfil'),
    path('perfil/<int:usuario_id>/editar/', views.PerfilEditarView.as_view(), name='perfil_editar'),
    path('perfil/<int:usuario_id>/listar/', views.PerfilListView.as_view(), name='perfil_listar'),
    path('perfil/<int:usuario_id>/criar/', views.PerfilCreateView.as_view(), name='perfil_criar'),
    path('grupo/', views.GrupoListView.as_view(), name='grupo_list'),
    path('grupo/criar/', views.GrupoCreateView.as_view(), name='grupo_criar'),
    path('grupo/editar/<int:pk>/', views.GrupoUpdateView.as_view(), name='grupo_editar'),
    path('grupo/excluir/<int:pk>/', views.GrupoDeleteView.as_view(), name='grupo_excluir'),
    path('usuario/', views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuario/criar/', views.UsuarioCreateView.as_view(), name='usuario_criar'),
    path('usuario/editar/<int:pk>/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuario/excluir/<int:pk>/', views.UsuarioDeleteView.as_view(), name='usuario_excluir'),

]