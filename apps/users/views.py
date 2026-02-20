from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q

from .models import CustomUser
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserUpdateForm,
    UserRoleUpdateForm,
    CustomPasswordChangeForm
)


# ============================================
# VUES FONCTIONNELLES (Function-Based Views)
# ============================================

def user_login(request):
    """
    Vue de connexion
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenue {user.get_full_name()} !')
            
            # Redirection selon le rôle
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            if user.is_admin() or user.is_manager():
                return redirect('dashboard:home')
            elif user.is_waiter():
                return redirect('orders:order_list')
            elif user.is_chef():
                return redirect('orders:kitchen_display')
            elif user.is_cashier():
                return redirect('orders:invoice_list')
            else:
                return redirect('dashboard:home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


def user_signup(request):
    """
    Vue d'inscription (Sign Up)
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Compte créé avec succès ! Bienvenue, {user.username}.')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Erreur lors de la création du compte. Veuillez vérifier les informations.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/signup.html', {'form': form})


@login_required
def user_logout(request):
    """
    Vue de déconnexion
    """
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('users:login')


@login_required
def user_profile(request):
    """
    Vue du profil de l'utilisateur connecté
    """
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('users:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'users/profile.html', context)


@login_required
def change_password(request):
    """
    Vue de changement de mot de passe
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Maintenir la session active
            messages.success(request, 'Votre mot de passe a été changé avec succès.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, 'users/change_password.html', {'form': form})


# ============================================
# VUES BASÉES SUR LES CLASSES (Class-Based Views)
# ============================================

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur est admin ou manager
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_users()
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('dashboard:home')


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    Liste de tous les utilisateurs (admin uniquement)
    """
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = CustomUser.objects.all()
        
        # Recherche
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Filtre par rôle
        role_filter = self.request.GET.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = CustomUser.ROLE_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        return context


class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """
    Détails d'un utilisateur (admin uniquement)
    """
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user_detail'


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """
    Création d'un nouvel utilisateur (admin uniquement)
    """
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur créé avec succès.')
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """
    Modification d'un utilisateur (admin uniquement)
    """
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_form'] = UserRoleUpdateForm(instance=self.object)
        return context
    
    def form_valid(self, form):
        # Traiter aussi le formulaire de rôle
        role_form = UserRoleUpdateForm(self.request.POST, instance=self.object)
        if role_form.is_valid():
            role_form.save()
        
        messages.success(self.request, 'Utilisateur modifié avec succès.')
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """
    Suppression d'un utilisateur (admin uniquement)
    """
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Utilisateur supprimé avec succès.')
        return super().delete(request, *args, **kwargs)