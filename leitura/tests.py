from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Livro, Resenha, Badge


GIF_1X1 = (
	b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
	b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class HomeViewTests(TestCase):
	def test_destaques_semana_mostra_tres_livros_mais_recentes(self):
		livros = []
		for indice in range(4):
			livro = Livro.objects.create(
				titulo=f'Livro {indice}',
				autor=f'Autor {indice}',
				sinopse='Sinopse de teste',
				capa=SimpleUploadedFile(f'capa_{indice}.gif', GIF_1X1, content_type='image/gif'),
			)
			livros.append(livro)

		response = self.client.get(reverse('home'))

		destaques = list(response.context['destaques_semana'])
		self.assertEqual([livro.pk for livro in destaques], [livros[3].pk, livros[2].pk, livros[1].pk])

	def test_progresso_usa_xp_total_ate_proxima_badge(self):
		user = User.objects.create_user(username='ana', password='senha12345')
		Badge.objects.create(nome='Iniciante', descricao='Primeira badge', xp_minimo=10)
		Badge.objects.create(nome='Leitor Dedicado', descricao='Segunda badge', xp_minimo=50)
		user.perfil.xp = 20
		user.perfil.save()

		self.client.login(username='ana', password='senha12345')
		response = self.client.get(reverse('home'))

		self.assertEqual(response.context['progress_current_xp'], 20)
		self.assertEqual(response.context['progress_target_xp'], 50)
		self.assertEqual(response.context['faltam_xp'], 30)

	def test_home_mostra_ate_seis_ultimas_resenhas(self):
		user = User.objects.create_user(username='maria', password='senha12345')
		livro = Livro.objects.create(
			titulo='Livro Base',
			autor='Autor Base',
			sinopse='Sinopse base',
			capa=SimpleUploadedFile('capa_base.gif', GIF_1X1, content_type='image/gif'),
		)

		for indice in range(7):
			Resenha.objects.create(
				livro=livro,
				usuario=user,
				texto=f'Resenha {indice}',
				nota=5,
			)

		response = self.client.get(reverse('home'))

		self.assertEqual(len(response.context['ultimas_resenhas']), 6)

	def test_biblioteca_retorna_pagina_de_livros(self):
		livro = Livro.objects.create(
			titulo='Biblioteca Teste',
			autor='Autor Biblioteca',
			sinopse='Livro para teste da biblioteca.',
			capa=SimpleUploadedFile('capa_biblioteca.gif', GIF_1X1, content_type='image/gif'),
		)

		response = self.client.get(reverse('biblioteca'))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'leitura/biblioteca.html')
		self.assertIn(livro, response.context['livros'])


class CadastroLivroTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='vinicius', password='senha12345')

	def test_usuario_precisa_estar_logado_para_cadastrar_livro(self):
		response = self.client.get(reverse('cadastrar_livro'))

		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login'), response.url)

	def test_cadastro_cria_livro_resenha_e_atualiza_xp(self):
		self.client.login(username='vinicius', password='senha12345')

		response = self.client.post(
			reverse('cadastrar_livro'),
			{
				'titulo': 'Novo Livro',
				'autor': 'Autor Teste',
				'sinopse': 'Uma sinopse completa para o livro.',
				'texto': 'Essa e a primeira resenha desse livro.',
				'nota': 5,
				'capa': SimpleUploadedFile('capa.gif', GIF_1X1, content_type='image/gif'),
			},
		)

		livro = Livro.objects.get(titulo='Novo Livro')
		resenha = Resenha.objects.get(livro=livro)

		self.user.refresh_from_db()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('detalhes_livro', args=[livro.pk]))
		self.assertEqual(resenha.usuario, self.user)
		self.assertEqual(resenha.nota, 5)
		self.assertEqual(self.user.perfil.xp, 10)
