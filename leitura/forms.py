from django import forms
from django.contrib.auth.models import User
from .models import Livro, Resenha, Perfil

class ResenhaForm(forms.ModelForm):
    class Meta:
        model = Resenha
        fields = ['texto', 'nota']
        widgets = {
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'O que você achou deste livro?'}),
            'nota': forms.Select(attrs={'class': 'form-select'}),
        }


class CadastroLivroForm(forms.ModelForm):
    texto = forms.CharField(
        label='Sua resenha',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Escreva a primeira resenha desse livro.',
            }
        ),
    )
    nota = forms.ChoiceField(
        label='Sua nota',
        choices=Resenha._meta.get_field('nota').choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Livro
        fields = ['titulo', 'autor', 'sinopse', 'capa']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titulo do livro'}),
            'autor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do autor'}),
            'sinopse': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Escreva uma sinopse clara e objetiva.',
                }
            ),
            'capa': forms.FileInput(attrs={'class': 'form-control modern-file-input', 'accept': 'image/*'}),
        }


class EditarPerfilForm(forms.ModelForm):
    """Form para editar informações básicas do perfil do usuário."""
    nome = forms.CharField(
        label='Nome completo',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome completo'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
    )

    class Meta:
        model = Perfil
        fields = ['foto_perfil']
        labels = {
            'foto_perfil': 'Foto de Perfil',
        }
        widgets = {
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control modern-file-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preencher campos do User se houver uma instância
        if self.instance and self.instance.usuario:
            self.fields['nome'].initial = self.instance.usuario.get_full_name() or self.instance.usuario.username
            self.fields['email'].initial = self.instance.usuario.email

    def save(self, commit=True):
        perfil = super().save(commit=False)
        # Salvar dados do User associado
        perfil.usuario.email = self.cleaned_data['email']
        perfil.usuario.first_name = self.cleaned_data['nome'].split()[0] if self.cleaned_data['nome'] else ''
        perfil.usuario.last_name = ' '.join(self.cleaned_data['nome'].split()[1:]) if len(self.cleaned_data['nome'].split()) > 1 else ''
        
        if commit:
            perfil.usuario.save()
            perfil.save()
        return perfil


class AlterarSenhaForm(forms.Form):
    """Form para alterar a senha do usuário."""
    senha_atual = forms.CharField(
        label='Senha atual',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Sua senha atual'}),
    )
    senha_nova = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nova senha'}),
        min_length=8,
    )
    senha_confirmacao = forms.CharField(
        label='Confirmar nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme a nova senha'}),
        min_length=8,
    )

    def clean(self):
        cleaned_data = super().clean()
        senha_nova = cleaned_data.get('senha_nova')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')

        if senha_nova and senha_confirmacao and senha_nova != senha_confirmacao:
            raise forms.ValidationError('As novas senhas não coincidem.')

        return cleaned_data