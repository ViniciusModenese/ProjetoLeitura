from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('biblioteca/', views.biblioteca, name='biblioteca'),
    path('livro/<int:pk>/', views.detalhes_livro, name='detalhes_livro'),
    path('livros/novo/', views.cadastrar_livro, name='cadastrar_livro'),
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),
]

