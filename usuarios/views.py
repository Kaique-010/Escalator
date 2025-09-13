from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from .models import Grupo, Permissao, Usuario, Perfil
from .forms import UsuarioForm, PerfilForm, GrupoForm, PermissaoForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, DetailView

class GrupoListView(ListView):
    model = Grupo
    template_name = 'usuarios/grupo_list.html'
    context_object_name = 'grupos'

class GrupoCreateView(CreateView):
    model = Grupo
    form_class = GrupoForm
    template_name = 'usuarios/grupo_form.html'
    success_url = '/usuarios/grupo/'

class GrupoUpdateView(UpdateView):
    model = Grupo
    form_class = GrupoForm
    template_name = 'usuarios/grupo_form.html'
    success_url = '/usuarios/grupo/'

class GrupoDeleteView(DeleteView):
    model = Grupo
    template_name = 'usuarios/grupo_confirm_delete.html'
    success_url = '/usuarios/grupo/'

class PermissaoListView(ListView):
    model = Permissao
    template_name = 'usuarios/permissao_list.html'
    context_object_name = 'permissoes'

class PermissaoCreateView(CreateView):
    model = Permissao
    form_class = PermissaoForm
    template_name = 'usuarios/permissao_form.html'
    success_url = '/usuarios/permissao/'

class PermissaoUpdateView(UpdateView):
    model = Permissao
    form_class = PermissaoForm
    template_name = 'usuarios/permissao_form.html'
    success_url = '/usuarios/permissao/'

class PermissaoDeleteView(DeleteView):
    model = Permissao
    template_name = 'usuarios/permissao_confirm_delete.html'
    success_url = '/usuarios/permissao/'

class UsuarioListView(ListView):
    model = Usuario
    template_name = 'usuarios/usuario_list.html'
    context_object_name = 'usuarios'

class UsuarioCreateView(CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = 'usuarios/usuario_form.html'
    success_url = '/usuarios/usuario/'

class UsuarioUpdateView(UpdateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = 'usuarios/usuario_form.html'
    success_url = '/usuarios/usuario/'

class UsuarioDeleteView(DeleteView):
    model = Usuario
    template_name = 'usuarios/usuario_confirm_delete.html'
    success_url = '/usuarios/usuario/'

class UsuarioDetailView(DetailView):
    model = Usuario
    template_name = 'usuarios/usuario_detail.html'
    context_object_name = 'usuario'
    pk_url_kwarg = 'usuario_id'
    queryset = Usuario.objects.all()

def registrar(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro realizado com sucesso!')
            return redirect('dashboard')
    else:
        form = UsuarioForm()
        messages.success(request, 'Preencha os campos corretamente!')
    return render(request, 'usuarios/registrar.html', {'form': form})  

class LoginView(LoginView):
    template_name = 'usuarios/login.html'
    success_url = '/dashboard/'
    
    def form_valid(self, form):
        print("=== DEBUG LOGIN VÁLIDO ===")
        print("Form cleaned_data:", form.cleaned_data)
        print("User autenticado:", form.get_user())
        print("Request user antes:", self.request.user)
        
        response = super().form_valid(form)
        
        print("Request user depois:", self.request.user)
        print("=== FIM DEBUG VÁLIDO ===")
        
        messages.success(self.request, 'Login realizado com sucesso!')
        return response
    
    def form_invalid(self, form):
        print("=== DEBUG LOGIN INVÁLIDO ===")
        print("Form errors:", form.errors)
        print("Form non_field_errors:", form.non_field_errors())
        print("Form cleaned_data:", getattr(form, 'cleaned_data', 'Não disponível'))
        print("=== FIM DEBUG INVÁLIDO ===")
        return super().form_invalid(form)
    def get_success_url(self):
        return self.success_url
    redirect_field_name = 'next'

class LogoutView(LogoutView):
    template_name = 'usuarios/logout.html'    
    next_page = '/'
    http_method_names = ['get', 'post']
    
    def get(self, request, *args, **kwargs):
        # Renderiza a página de confirmação de logout
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        messages.success(request, 'Logout realizado com sucesso!')
        return super().post(request, *args, **kwargs)

class PerfilDetailView(DetailView):
    model = Perfil
    template_name = 'usuarios/perfil.html'
    context_object_name = 'usuario'
    pk_url_kwarg = 'usuario_id'
    queryset = Usuario.objects.all()

class PerfilEditarView(UpdateView):
    model = Perfil
    form_class = PerfilForm
    template_name = 'usuarios/perfil_editar.html'
    context_object_name = 'usuario'
    pk_url_kwarg = 'usuario_id'
    queryset = Usuario.objects.all()
    def get_success_url(self):
        return reverse('perfil', kwargs={'usuario_id': self.object.usuario.id})

class PerfilListView(ListView):
    model = Perfil
    template_name = 'usuarios/perfil_list.html'
    context_object_name = 'perfis'
    queryset = Perfil.objects.all()
    def get_queryset(self):
        return Perfil.objects.filter(usuario=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.request.user
        return context

class PerfilCreateView(CreateView):
    model = Perfil
    form_class = PerfilForm
    template_name = 'usuarios/perfil_criar.html'
    context_object_name = 'usuario'
    pk_url_kwarg = 'usuario_id'
    queryset = Usuario.objects.all()
    def get_success_url(self):
        return reverse('perfil', kwargs={'usuario_id': self.object.usuario.id})
    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario'] = self.request.user
        return context