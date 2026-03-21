from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, update_session_auth_hash
from .models import Livro, Perfil, Badge, Resenha
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Avg, Count
from django.db.models.functions import ExtractMonth
from django.contrib.auth.decorators import login_required
from .forms import ResenhaForm, CadastroLivroForm, EditarPerfilForm, AlterarSenhaForm, CadastroUsuarioForm
from datetime import datetime


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
            livro = form.save(commit=False)
            livro.criador = request.user
            livro.save()
            Resenha.objects.create(
                livro=livro,
                usuario=request.user,
                texto=form.cleaned_data['texto'],
                nota=form.cleaned_data['nota'],
            )
            # 100 XP por adicionar um livro + 10 XP pela resenha obrigatória.
            atualizar_xp_e_badges(request.user, xp_ganho=110)
            return redirect('detalhes_livro', pk=livro.pk)

    return render(request, 'leitura/cadastrar_livro.html', {'form': form})

class CadastroView(generic.CreateView):
    form_class = CadastroUsuarioForm
    success_url = reverse_lazy('login')
    template_name = 'registration/cadastro.html'


@login_required
def minhas_metas(request):
    perfil = request.user.perfil
    ano_atual = datetime.now().year

    livros_no_site_ano = Livro.objects.filter(criador=request.user, data_cadastro__year=ano_atual).count()
    livros_lidos_informados = perfil.livros_lidos
    livros_ano = livros_no_site_ano + livros_lidos_informados
    resenhas_ano = Resenha.objects.filter(usuario=request.user, data_postagem__year=ano_atual).count()

    meta_livros = max(1, perfil.meta_livros_ano)
    meta_resenhas = max(1, perfil.meta_resenhas)

    livros_percent = min(int((livros_ano / meta_livros) * 100), 100)
    resenhas_percent = min(int((resenhas_ano / meta_resenhas) * 100), 100)
    faltam_livros = max(meta_livros - livros_ano, 0)
    faltam_resenhas = max(meta_resenhas - resenhas_ano, 0)

    livros_mes_qs = (
        Livro.objects.filter(criador=request.user, data_cadastro__year=ano_atual)
        .annotate(mes=ExtractMonth('data_cadastro'))
        .values('mes')
        .annotate(total=Count('id'))
    )
    resenhas_mes_qs = (
        Resenha.objects.filter(usuario=request.user, data_postagem__year=ano_atual)
        .annotate(mes=ExtractMonth('data_postagem'))
        .values('mes')
        .annotate(total=Count('id'))
    )

    livros_por_mes = [0] * 12
    resenhas_por_mes = [0] * 12

    for item in livros_mes_qs:
        livros_por_mes[int(item['mes']) - 1] = item['total']

    for item in resenhas_mes_qs:
        resenhas_por_mes[int(item['mes']) - 1] = item['total']

    max_livros_mes = max(livros_por_mes) if any(livros_por_mes) else 1
    max_resenhas_mes = max(resenhas_por_mes) if any(resenhas_por_mes) else 1

    livros_mes_percent = [int((v / max_livros_mes) * 100) for v in livros_por_mes]
    resenhas_mes_percent = [int((v / max_resenhas_mes) * 100) for v in resenhas_por_mes]

    total_badges = Badge.objects.count()
    badges_desbloqueadas = perfil.badges.count()
    badge_percent = min(int((badges_desbloqueadas / total_badges) * 100), 100) if total_badges > 0 else 0

    livros_barras = []
    resenhas_barras = []
    meses_labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    for i in range(12):
        livros_barras.append({
            'mes': meses_labels[i],
            'total': livros_por_mes[i],
            'percent': livros_mes_percent[i],
        })
        resenhas_barras.append({
            'mes': meses_labels[i],
            'total': resenhas_por_mes[i],
            'percent': resenhas_mes_percent[i],
        })

    context = {
        'ano_atual': ano_atual,
        'meta_livros': meta_livros,
        'meta_resenhas': meta_resenhas,
        'livros_ano': livros_ano,
        'livros_no_site_ano': livros_no_site_ano,
        'livros_lidos_informados': livros_lidos_informados,
        'resenhas_ano': resenhas_ano,
        'livros_percent': livros_percent,
        'resenhas_percent': resenhas_percent,
        'faltam_livros': faltam_livros,
        'faltam_resenhas': faltam_resenhas,
        'livros_barras': livros_barras,
        'resenhas_barras': resenhas_barras,
        'total_badges': total_badges,
        'badges_desbloqueadas': badges_desbloqueadas,
        'badge_percent': badge_percent,
    }
    return render(request, 'leitura/metas.html', context)


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

    all_badges = list(Badge.objects.order_by('xp_minimo', 'id')[:10])
    owned_badge_ids = list(perfil_obj.badges.values_list('id', flat=True))

    # Garante uma grade fixa de 10 slots, mesmo se houver menos badges cadastradas.
    if len(all_badges) < 10:
        all_badges.extend([None] * (10 - len(all_badges)))

    resenhas_count = Resenha.objects.filter(usuario=request.user).count()
    livros_adicionados_count = Livro.objects.filter(criador=request.user).count()

    context = {
        'perfil': perfil_obj,
        'form_perfil': form_perfil,
        'form_senha': form_senha,
        'mensagem': mensagem,
        'tipo_mensagem': tipo_mensagem,
        'all_badges': all_badges,
        'owned_badge_ids': owned_badge_ids,
        'resenhas_count': resenhas_count,
        'livros_adicionados_count': livros_adicionados_count,
    }
    return render(request, 'leitura/perfil.html', context)