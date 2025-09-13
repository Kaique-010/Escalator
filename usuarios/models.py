from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.models import Group, Permission

class Permissao(models.Model):
    nome = models.CharField(max_length=100, null=False, blank=False)
    descricao = models.CharField(max_length=100, null=False, blank=False)
    class Meta:
        db_table = 'permissao'
        verbose_name = 'permissao'
        verbose_name_plural = 'permissoes'

class Grupo(models.Model):
    nome = models.CharField(max_length=100, null=False, blank=False)
    permissoes = models.ManyToManyField(Permission, blank=True)
    class Meta:
        db_table = 'grupo'
        verbose_name = 'grupo'
        verbose_name_plural = 'grupos'



class Usuario(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    username = models.CharField(max_length=100, unique=True, null=False, blank=False)
    password = models.CharField(max_length=100, null=False, blank=False)
    first_name = models.CharField(max_length=100, null=False, blank=False)
    last_name = models.CharField(max_length=100, null=False, blank=False)
    date_joined = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    last_login = models.DateTimeField(auto_now=True, null=False, blank=False)
    is_active = models.BooleanField(default=True, null=False, blank=False)
    is_staff = models.BooleanField(default=False, null=False, blank=False)
    is_superuser = models.BooleanField(default=False, null=False, blank=False)
    groups = models.ManyToManyField('auth.Group', blank=True, null=False)
    user_permissions = models.ManyToManyField('auth.Permission', blank=True, null=False)

    class Meta:
        db_table = 'usuario'
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'


class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    telefone = models.CharField(max_length=100, null=False, blank=False)
    endereco = models.CharField(max_length=100, null=False, blank=False)
    cidade = models.CharField(max_length=100, null=False, blank=False)
    pais = models.CharField(max_length=100, null=False, blank=False)
    data_nascimento = models.DateField(null=False, blank=False)
    genero = models.CharField(max_length=100, null=False, blank=False)
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, null=True, blank=True)
    permissoes = models.ManyToManyField(Permissao, blank=True)
    
    class Meta:
        db_table = 'perfil'
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

