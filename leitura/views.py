from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, update_session_auth_hash
from .models import Livro, Perfil, Badge, Resenha
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required
from .forms import ResenhaForm, CadastroLivroForm, EditarPerfilForm, AlterarSenhaForm


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


@login_required
def perfil(request):
    """View para exibir e editar o perfil do usuário."""
    perfil_obj = request.user.perfil
    form_perfil = None
    form_senha = None
    mensagem = ''
    tipo_mensagem = ''

    if request.method == 'POST':
        if 'editar_perfil' in request.POST:
            form_perfil = EditarPerfilForm(request.POST, request.FILES, instance=perfil_obj)
            if form_perfil.is_valid():
                form_perfil.save()
                mensagem = 'Perfil atualizado com sucesso!'
                tipo_mensagem = 'success'
                # Recarregar para exibir valores atualizados
                perfil_obj.refresh_from_db()
                request.user.refresh_from_db()
            else:
                tipo_mensagem = 'danger'
                mensagem = 'Erro ao atualizar perfil.'
        
        elif 'alterar_senha' in request.POST:
            form_senha = AlterarSenhaForm(request.POST)
            if form_senha.is_valid():
                senha_atual = form_senha.cleaned_data['senha_atual']
                # Verificar se a senha atual está correta
                if request.user.check_password(senha_atual):
                    request.user.set_password(form_senha.cleaned_data['senha_nova'])
                    request.user.save()
                    # Manter o usuário logado após alterar a senha
                    update_session_auth_hash(request, request.user)
                    mensagem = 'Senha alterada com sucesso!'
                    tipo_mensagem = 'success'
                    form_senha = AlterarSenhaForm()  # Limpar o form
                else:
                    form_senha.add_error('senha_atual', 'Senha atual incorreta.')
                    tipo_mensagem = 'danger'
                    mensagem = 'A senha atual está incorreta.'
            else:
                tipo_mensagem = 'danger'
                mensagem = 'Erro ao alterar senha.'
    
    if not form_perfil:
        form_perfil = EditarPerfilForm(instance=perfil_obj)
    if not form_senha:
        form_senha = AlterarSenhaForm()

    context = {
        'perfil': perfil_obj,
        'form_perfil': form_perfil,
        'form_senha': form_senha,
        'mensagem': mensagem,
        'tipo_mensagem': tipo_mensagem,
    }
    return render(request, 'leitura/perfil.html', context)