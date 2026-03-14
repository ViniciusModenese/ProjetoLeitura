from django import forms
from .models import Resenha

class ResenhaForm(forms.ModelForm):
    class Meta:
        model = Resenha
        fields = ['texto', 'nota']
        widgets = {
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'O que você achou deste livro?'}),
            'nota': forms.Select(attrs={'class': 'form-select'}),
        }