from django.utils import timezone

from .models import Perfil


class OfensivaMiddleware:
    """Atualiza a ofensiva diaria do usuario autenticado em cada request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                perfil = request.user.perfil
            except Perfil.DoesNotExist:
                perfil = Perfil.objects.create(usuario=request.user)

            agora = timezone.now()
            mudou_ofensiva = False

            if perfil.ultimo_acesso_ofensiva is None:
                perfil.ofensiva_atual = 1
                mudou_ofensiva = True
            else:
                intervalo = agora - perfil.ultimo_acesso_ofensiva
                if intervalo.total_seconds() > 86400:
                    perfil.ofensiva_atual = 1
                    mudou_ofensiva = True
                else:
                    ultimo_dia = timezone.localtime(perfil.ultimo_acesso_ofensiva).date()
                    hoje = timezone.localdate()
                    if ultimo_dia != hoje:
                        perfil.ofensiva_atual += 1
                        mudou_ofensiva = True

            perfil.ultimo_acesso_ofensiva = agora
            if mudou_ofensiva:
                perfil.save(update_fields=['ofensiva_atual', 'ultimo_acesso_ofensiva'])
            else:
                perfil.save(update_fields=['ultimo_acesso_ofensiva'])

        return self.get_response(request)
