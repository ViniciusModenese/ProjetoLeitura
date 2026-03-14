from django.shortcuts import render, get_object_or_404, redirect
from .models import Livro, Perfil
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from .forms import ResenhaForm
from django.contrib.auth.decorators import login_required

def home(request):
    livros = Livro.objects.all()
    return render(request, 'leitura/home.html', {'livros': livros})

def detalhes_livro(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    form = ResenhaForm()

    if request.method == 'POST' and request.user.is_authenticated:
        form = ResenhaForm(request.POST)
        if form.is_valid():
            resenha = form.save(commit=False)
            resenha.livro = livro
            resenha.usuario = request.user
            resenha.save()

            # Lógica de Gamificação: +10 XP por resenha
            perfil = request.user.perfil
            perfil.xp += 10
            perfil.save()

            return redirect('detalhes_livro', pk=pk)

    return render(request, 'leitura/detalhes.html', {'livro': livro, 'form': form})

class CadastroView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/cadastro.html'