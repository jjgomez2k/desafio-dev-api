"""
Configuração de URL do wallet_api_challenge

A lista `urlpatterns` roteia URLs para views. Para mais informações, veja:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Exemplos:
Views baseadas em função
    1. Adicione um import: from my_app import views
    2. Adicione uma URL para urlpatterns: path('blog/', views.home, name='home')
Views baseadas em classe
    1. Adicione um import: from other_app.views import Home
    2. Adicione uma URL para urlpatterns: path('blog/', Home.as_view(), name='home')
Incluindo outra URLconf
    1. Importe a função include(): from django.urls import include, path
    2. Adicione uma URL para urlpatterns: path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Rotas para autenticação JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Inclui as URLs do nosso aplicativo wallet_app
    path('api/', include('wallet_app.urls')),
]
