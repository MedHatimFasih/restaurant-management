from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import Category, MenuItem
from .forms import CategoryForm, MenuItemForm, MenuItemSearchForm


# ============================================
# MIXINS DE PERMISSIONS
# ============================================

class MenuManagerMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur peut gérer le menu
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_menu()
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission de gérer le menu.")
        return redirect('menu:menu_list')


# ============================================
# VUES POUR LES CATÉGORIES
# ============================================

class CategoryListView(LoginRequiredMixin, MenuManagerMixin, ListView):
    """
    Liste de toutes les catégories
    """
    model = Category
    template_name = 'menu/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.annotate(
            items_count=Count('items')
        ).order_by('order', 'name')


class CategoryCreateView(LoginRequiredMixin, MenuManagerMixin, CreateView):
    """
    Créer une nouvelle catégorie
    """
    model = Category
    form_class = CategoryForm
    template_name = 'menu/category_form.html'
    success_url = reverse_lazy('menu:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Catégorie créée avec succès.')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, MenuManagerMixin, UpdateView):
    """
    Modifier une catégorie
    """
    model = Category
    form_class = CategoryForm
    template_name = 'menu/category_form.html'
    success_url = reverse_lazy('menu:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Catégorie modifiée avec succès.')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, MenuManagerMixin, DeleteView):
    """
    Supprimer une catégorie
    """
    model = Category
    template_name = 'menu/category_confirm_delete.html'
    success_url = reverse_lazy('menu:category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Catégorie supprimée avec succès.')
        return super().delete(request, *args, **kwargs)


# ============================================
# VUES POUR LES PLATS
# ============================================

class MenuItemListView(LoginRequiredMixin, ListView):
    """
    Liste de tous les plats avec filtres et recherche
    """
    model = MenuItem
    template_name = 'menu/menu_list.html'
    context_object_name = 'menu_items'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = MenuItem.objects.select_related('category').all()
        
        # Recherche par nom ou description
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filtre par catégorie
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filtre par disponibilité
        availability = self.request.GET.get('availability')
        if availability == 'available':
            queryset = queryset.filter(is_available=True)
        elif availability == 'unavailable':
            queryset = queryset.filter(is_available=False)
        
        # Filtres diététiques
        dietary = self.request.GET.getlist('dietary')
        if 'vegetarian' in dietary:
            queryset = queryset.filter(is_vegetarian=True)
        if 'vegan' in dietary:
            queryset = queryset.filter(is_vegan=True)
        if 'spicy' in dietary:
            queryset = queryset.filter(is_spicy=True)
        
        return queryset.order_by('category__order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = MenuItemSearchForm(self.request.GET)
        context['categories'] = Category.objects.filter(is_active=True).order_by('order')
        context['total_items'] = MenuItem.objects.count()
        context['available_items'] = MenuItem.objects.filter(is_available=True).count()
        return context


class MenuItemDetailView(LoginRequiredMixin, DetailView):
    """
    Détails d'un plat
    """
    model = MenuItem
    template_name = 'menu/menu_detail.html'
    context_object_name = 'item'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


class MenuItemCreateView(LoginRequiredMixin, MenuManagerMixin, CreateView):
    """
    Créer un nouveau plat
    """
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'menu/menu_form.html'
    success_url = reverse_lazy('menu:menu_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Plat créé avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter un plat'
        return context


class MenuItemUpdateView(LoginRequiredMixin, MenuManagerMixin, UpdateView):
    """
    Modifier un plat
    """
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'menu/menu_form.html'
    success_url = reverse_lazy('menu:menu_list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def form_valid(self, form):
        messages.success(self.request, 'Plat modifié avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier le plat'
        return context


class MenuItemDeleteView(LoginRequiredMixin, MenuManagerMixin, DeleteView):
    """
    Supprimer un plat
    """
    model = MenuItem
    template_name = 'menu/menu_confirm_delete.html'
    success_url = reverse_lazy('menu:menu_list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Plat supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


# ============================================
# VUES AJAX
# ============================================

@login_required
def toggle_availability(request, slug):
    """
    Activer/désactiver la disponibilité d'un plat (AJAX)
    """
    if not request.user.can_manage_menu():
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    if request.method == 'POST':
        item = get_object_or_404(MenuItem, slug=slug)
        item.is_available = not item.is_available
        item.save()
        
        return JsonResponse({
            'success': True,
            'is_available': item.is_available,
            'message': f'{item.name} est maintenant {"disponible" if item.is_available else "indisponible"}'
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def menu_public(request):
    """
    Menu public pour les serveurs (prise de commande)
    """
    categories = Category.objects.filter(
        is_active=True
    ).prefetch_related('items').order_by('order')
    
    # Filtrer uniquement les plats disponibles pour chaque catégorie
    for category in categories:
        category.available_items = category.items.filter(is_available=True)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'menu/menu_public.html', context)