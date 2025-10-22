from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('escalator.urls')),  # APIs REST do sistema de escalas
    path('dashboard/', include('escalator.urls')),
    path('usuarios/', include('usuarios.urls')),
]
