from django import forms
from .models import Livro, Resenha

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
            'capa': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }