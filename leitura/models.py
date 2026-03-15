from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=150)
    sinopse = models.TextField()
    capa = models.ImageField(upload_to='capas/') 
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Resenha(models.Model):
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='resenhas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    nota = models.IntegerField(choices=[(i, i) for i in range(1, 6)]) 
    data_postagem = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resenha de {self.usuario.username} para {self.livro.titulo}"

class Badge(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    # Trocamos o campo de ícone (texto) por um ImageField
    imagem = models.ImageField(upload_to='badges/', null=True, blank=True)
    xp_minimo = models.IntegerField(default=0)

    def __str__(self):
        return self.nome

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    xp = models.IntegerField(default=0)
    livros_lidos = models.IntegerField(default=0)
    badges = models.ManyToManyField(Badge, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)