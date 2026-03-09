from django.shortcuts import render
from .models import Livro

def home(request):
    # Busca todos os livros cadastrados no banco de dados
    livros = Livro.objects.all()
    # Envia essa lista para o arquivo HTML (Template)
    return render(request, 'leitura/home.html', {'livros': livros})