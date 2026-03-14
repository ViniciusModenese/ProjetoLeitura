from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('livro/<int:pk>/', views.detalhes_livro, name='detalhes_livro'),
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),
]

