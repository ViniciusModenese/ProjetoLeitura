from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, update_session_auth_hash
from .models import Livro, Perfil, Badge, Resenha
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Avg, Count, Prefetch
from django.db.models import OuterRef, Subquery
from django.db.models.functions import ExtractMonth
from django.contrib.auth.decorators import login_required
from .forms import ResenhaForm, CadastroLivroForm, EditarPerfilForm, AlterarSenhaForm, CadastroUsuarioForm
from datetime import datetime
import unicodedata


def badges_nivel_qs():
    return Badge.objects.filter(nome__startswith='Nivel ').order_by('xp_minimo', 'id')


def _normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', (texto or ''))
    texto = ''.join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.lower()


def _categoria_dinamica_livro(livro):
    base = _normalizar_texto(f"{livro.titulo} {livro.sinopse}")

    regras = [
        ('quero_desidratar_de_chorar', 'Quero desidratar de chorar', ['triste', 'dor', 'perda', 'lagrima', 'emocion', 'drama']),
        ('quero_dormir_de_luz_acesa', 'Quero dormir de luz acesa', ['terror', 'horror', 'medo', 'sombr', 'monstro', 'assust']),
        ('quero_fugir_pra_outro_mundo', 'Quero fugir pra outro mundo', ['fantasia', 'magia', 'elfo', 'dragao', 'reino', 'mitolog']),
        ('quero_viajar_pro_impossivel', 'Quero viajar pro impossivel', ['ficcao cientifica', 'futuro', 'espaco', 'distop', 'rob', 'tecnolog']),
        ('quero_brincar_de_detetive', 'Quero brincar de detetive', ['misterio', 'investiga', 'crime', 'detetive', 'enigma']),
        ('quero_adrenalina_em_cada_capitulo', 'Quero adrenalina em cada capitulo', ['aventur', 'jornada', 'guerra', 'sobreviv', 'batalha']),
        ('quero_borboletas_no_estomago', 'Quero borboletas no estomago', ['amor', 'romance', 'apaixon', 'relacion']),
        ('quero_parecer_culto_sem_esforco', 'Quero parecer culto sem esforco', ['filosof', 'politic', 'classico', 'sociedade', 'reflex']),
        ('quero_colocar_a_vida_nos_trilhos', 'Quero colocar a vida nos trilhos', ['desenvolvimento pessoal', 'habito', 'mindset', 'sucesso', 'autoconhecimento']),
    ]

    for slug, nome, pistas in regras:
        if any(pista in base for pista in pistas):
            return slug, nome

    return 'quero_uma_historia_que_me_prenda', 'Quero uma historia que me prenda'


def _ano_lancamento_livro(livro):
    if livro.ano_publicacao and 1400 <= livro.ano_publicacao <= datetime.now().year + 1:
        return livro.ano_publicacao
    return None


def _icone_categoria(slug):
    icones = {
        'quero_desidratar_de_chorar': 'bi-emoji-tear-fill',
        'quero_dormir_de_luz_acesa': 'bi-moon-stars-fill',
        'quero_fugir_pra_outro_mundo': 'bi-magic',
        'quero_viajar_pro_impossivel': 'bi-rocket-takeoff-fill',
        'quero_brincar_de_detetive': 'bi-search-heart-fill',
        'quero_adrenalina_em_cada_capitulo': 'bi-lightning-charge-fill',
        'quero_borboletas_no_estomago': 'bi-heart-fill',
        'quero_parecer_culto_sem_esforco': 'bi-journal-richtext',
        'quero_colocar_a_vida_nos_trilhos': 'bi-compass-fill',
        'quero_uma_historia_que_me_prenda': 'bi-bookmark-star-fill',
    }
    return icones.get(slug, 'bi-bookmark-star-fill')


def sincronizar_badges_nivel(perfil):
    """Mantem as badges de nivel coerentes com o XP atual do perfil."""
    badges_nivel = list(badges_nivel_qs())
    if not badges_nivel:
        return

    ids_desbloqueadas = {b.id for b in badges_nivel if b.xp_minimo <= perfil.xp}
    ids_nivel = {b.id for b in badges_nivel}
    ids_atuais_nivel = set(perfil.badges.filter(id__in=ids_nivel).values_list('id', flat=True))

    ids_para_add = ids_desbloqueadas - ids_atuais_nivel
    ids_para_remove = ids_atuais_nivel - ids_desbloqueadas

    if ids_para_add:
        perfil.badges.add(*Badge.objects.filter(id__in=ids_para_add))
    if ids_para_remove:
        perfil.badges.remove(*Badge.objects.filter(id__in=ids_para_remove))


def atualizar_xp_e_badges(usuario, xp_ganho=10):
    perfil = usuario.perfil
    perfil.xp += xp_ganho
    perfil.save()
    sincronizar_badges_nivel(perfil)

def home(request):
    livros = Livro.objects.annotate(
        media_notas=Avg('resenhas__nota'),
        total_resenhas=Count('resenhas'),
    ).order_by('-data_cadastro')

    destaques_semana = livros[:3]
    # Pega apenas 1 resenha por livro (a mais recente de cada livro), e então exibe as mais recentes entre elas.
    ultima_resenha_por_livro = Livro.objects.annotate(
        ultima_resenha_id=Subquery(
            Resenha.objects.filter(livro=OuterRef('pk')).order_by('-data_postagem').values('id')[:1]
        )
    ).filter(ultima_resenha_id__isnull=False).values('ultima_resenha_id')

    ultimas_resenhas = Resenha.objects.select_related('usuario', 'livro').filter(
        id__in=Subquery(ultima_resenha_por_livro)
    ).order_by('-data_postagem')[:6]

    user_badges_map = {}
    if ultimas_resenhas:
        user_ids = list({r.usuario_id for r in ultimas_resenhas})
        perfis_resenhas = Perfil.objects.filter(usuario_id__in=user_ids).prefetch_related(
            Prefetch('badges', queryset=badges_nivel_qs(), to_attr='badges_nivel_prefetched')
        )
        for perfil_item in perfis_resenhas:
            badge_usuario = perfil_item.badges_nivel_prefetched[-1] if perfil_item.badges_nivel_prefetched else None
            user_badges_map[perfil_item.usuario_id] = badge_usuario

    xp_atual = 0
    proxima_badge = None
    faltam_xp = 0
    progress_percent = 0
    progress_current_xp = 0
    progress_target_xp = 0
    ultima_badge_nivel = None

    if request.user.is_authenticated:
        perfil = request.user.perfil
        sincronizar_badges_nivel(perfil)
        xp_atual = perfil.xp
        proxima_badge = badges_nivel_qs().filter(xp_minimo__gt=xp_atual).first()

        if proxima_badge:
            faltam_xp = proxima_badge.xp_minimo - xp_atual
            progress_current_xp = xp_atual
            progress_target_xp = proxima_badge.xp_minimo
            progress_percent = min(int((xp_atual / proxima_badge.xp_minimo) * 100), 100) if proxima_badge.xp_minimo > 0 else 100
        elif xp_atual > 0:
            progress_percent = 100
            progress_current_xp = xp_atual
            progress_target_xp = xp_atual

        ultima_badge_nivel = perfil.badges.filter(nome__startswith='Nivel ').order_by('xp_minimo', 'id').last()

    context = {
        'destaques_semana': destaques_semana,
        'ultimas_resenhas': ultimas_resenhas,
        'xp_atual': xp_atual,
        'proxima_badge': proxima_badge,
        'faltam_xp': faltam_xp,
        'progress_percent': progress_percent,
        'progress_current_xp': progress_current_xp,
        'progress_target_xp': progress_target_xp,
        'ultima_badge_nivel': ultima_badge_nivel,
        'user_badges_map': user_badges_map,
    }
    return render(request, 'leitura/home.html', context)


def biblioteca(request):
    categoria_selecionada = (request.GET.get('categoria') or '').strip()
    ano_selecionado = (request.GET.get('ano') or '').strip()

    livros_base = list(
        Livro.objects.annotate(media_nota=Avg('resenhas__nota')).order_by('-data_cadastro')
    )
    categorias = {}
    anos = set()

    for livro in livros_base:
        cat_slug, cat_nome = _categoria_dinamica_livro(livro)
        ano = _ano_lancamento_livro(livro)

        livro.categoria_slug = cat_slug
        livro.categoria_nome = cat_nome
        livro.categoria_icone = _icone_categoria(cat_slug)
        livro.ano_lancamento = ano

        categorias[cat_slug] = cat_nome
        if ano:
            anos.add(ano)

    livros_filtrados = livros_base
    if categoria_selecionada:
        livros_filtrados = [l for l in livros_filtrados if getattr(l, 'categoria_slug', '') == categoria_selecionada]

    if ano_selecionado and ano_selecionado.isdigit():
        ano_int = int(ano_selecionado)
        livros_filtrados = [l for l in livros_filtrados if getattr(l, 'ano_lancamento', None) == ano_int]

    categorias_ordenadas = sorted(categorias.items(), key=lambda item: item[1])
    categorias_disponiveis = [
        (slug, nome, _icone_categoria(slug))
        for slug, nome in categorias_ordenadas
    ]

    context = {
        'livros': livros_filtrados,
        'categorias_disponiveis': categorias_disponiveis,
        'anos_disponiveis': sorted(anos, reverse=True),
        'categoria_selecionada': categoria_selecionada,
        'ano_selecionado': int(ano_selecionado) if ano_selecionado.isdigit() else None,
    }
    return render(request, 'leitura/biblioteca.html', context)

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
    ritmo_literario = perfil.ofensiva_atual
    meta_ritmo = 100
    ritmo_percent = min(int((ritmo_literario / meta_ritmo) * 100), 100)
    faltam_ritmo = max(meta_ritmo - ritmo_literario, 0)

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
        'ritmo_literario': ritmo_literario,
        'meta_ritmo': meta_ritmo,
        'ritmo_percent': ritmo_percent,
        'faltam_ritmo': faltam_ritmo,
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
    sincronizar_badges_nivel(perfil_obj)
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

    all_badges = list(badges_nivel_qs()[:10])
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