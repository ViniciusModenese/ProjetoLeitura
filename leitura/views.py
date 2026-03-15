from django.shortcuts import render, get_object_or_404, redirect
from .models import Livro, Perfil, Badge, Resenha
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required
from .forms import ResenhaForm, CadastroLivroForm


def atualizar_xp_e_badges(usuario, xp_ganho=10):
    perfil = usuario.perfil
    perfil.xp += xp_ganho
    perfil.save()

    badges_disponiveis = Badge.objects.filter(xp_minimo__lte=perfil.xp)
    for badge in badges_disponiveis:
        if badge not in perfil.badges.all():
            perfil.badges.add(badge)

def home(request):
    livros = Livro.objects.annotate(
        media_notas=Avg('resenhas__nota'),
        total_resenhas=Count('resenhas'),
    ).order_by('-data_cadastro')

    destaques_semana = livros[:3]
    ultimas_resenhas = Resenha.objects.select_related('usuario', 'livro').order_by('-data_postagem')[:6]

    xp_atual = 0
    proxima_badge = None
    faltam_xp = 0
    progress_percent = 0
    progress_current_xp = 0
    progress_target_xp = 0

    if request.user.is_authenticated:
        perfil = request.user.perfil
        xp_atual = perfil.xp
        proxima_badge = Badge.objects.filter(xp_minimo__gt=xp_atual).order_by('xp_minimo').first()

        if proxima_badge:
            faltam_xp = proxima_badge.xp_minimo - xp_atual
            progress_current_xp = xp_atual
            progress_target_xp = proxima_badge.xp_minimo
            progress_percent = min(int((xp_atual / proxima_badge.xp_minimo) * 100), 100) if proxima_badge.xp_minimo > 0 else 100
        elif xp_atual > 0:
            progress_percent = 100
            progress_current_xp = xp_atual
            progress_target_xp = xp_atual

    context = {
        'destaques_semana': destaques_semana,
        'ultimas_resenhas': ultimas_resenhas,
        'xp_atual': xp_atual,
        'proxima_badge': proxima_badge,
        'faltam_xp': faltam_xp,
        'progress_percent': progress_percent,
        'progress_current_xp': progress_current_xp,
        'progress_target_xp': progress_target_xp,
    }
    return render(request, 'leitura/home.html', context)


def biblioteca(request):
    livros = Livro.objects.order_by('-data_cadastro')
    return render(request, 'leitura/biblioteca.html', {'livros': livros})

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

            atualizar_xp_e_badges(request.user)

            return redirect('detalhes_livro', pk=pk)

    return render(request, 'leitura/detalhes.html', {'livro': livro, 'form': form})


@login_required
def cadastrar_livro(request):
    form = CadastroLivroForm()

    if request.method == 'POST':
        form = CadastroLivroForm(request.POST, request.FILES)
        if form.is_valid():
            livro = form.save()
            Resenha.objects.create(
                livro=livro,
                usuario=request.user,
                texto=form.cleaned_data['texto'],
                nota=form.cleaned_data['nota'],
            )
            atualizar_xp_e_badges(request.user)
            return redirect('detalhes_livro', pk=livro.pk)

    return render(request, 'leitura/cadastrar_livro.html', {'form': form})

class CadastroView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/cadastro.html'