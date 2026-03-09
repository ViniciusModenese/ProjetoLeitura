from django.db import models
from django.contrib.auth.models import User

class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=150)
    sinopse = models.TextField()
    capa = models.ImageField(upload_to='capas/') # Aqui usamos o Pillow que instalamos
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Resenha(models.Model):
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='resenhas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    nota = models.IntegerField(choices=[(i, i) for i in range(1, 6)]) # Notas de 1 a 5
    data_postagem = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resenha de {self.usuario.username} para {self.livro.titulo}"