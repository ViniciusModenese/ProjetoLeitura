from django.contrib import admin
from .models import Livro, Resenha, Perfil, Badge

admin.site.register(Livro)
admin.site.register(Resenha)
admin.site.register(Perfil)
admin.site.register(Badge)