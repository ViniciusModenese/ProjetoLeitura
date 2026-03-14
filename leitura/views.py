from django.shortcuts import render
from .models import Livro

def home(request):
    livros = Livro.objects.all()
    return render(request, 'leitura/home.html', {'livros': livros})