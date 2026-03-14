from django.shortcuts import render, get_object_or_404
from .models import Livro

def home(request):
    livros = Livro.objects.all()
    return render(request, 'leitura/home.html', {'livros': livros})

def detalhes_livro(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    return render(request, 'leitura/detalhes.html', {'livro': livro})