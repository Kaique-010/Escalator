from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Perfil, Grupo, Permissao

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nome', 'permissoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'permissoes': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

class PermissaoForm(forms.ModelForm):
    class Meta:
        model = Permissao
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }



class UsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['telefone', 'endereco', 'cidade', 'pais', 'data_nascimento', 'genero', 'foto', 'grupo', 'permissoes']
        widgets = {
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control'}),
            'genero': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'grupo': forms.Select(attrs={'class': 'form-control'}),
            'permissoes': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
