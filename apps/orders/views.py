from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from decimal import Decimal

from .models import Order, OrderItem, Invoice
from .forms import OrderForm, OrderItemForm, OrderSearchForm, InvoiceForm, DiscountForm
from apps.tables.models import Table
from apps.menu.models import MenuItem


# ============================================
# MIXINS DE PERMISSIONS
# ============================================

class WaiterRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur peut prendre des commandes
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_take_orders()
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission de gérer les commandes.")
        return redirect('dashboard:home')


class CashierRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur est caissier
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_cashier() or 
            self.request.user.is_manager() or 
            self.request.user.is_admin()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission d'accéder à la caisse.")
        return redirect('dashboard:home')


# ============================================
# VUES POUR LES COMMANDES
# ============================================

class OrderListView(LoginRequiredMixin, WaiterRequiredMixin, ListView):
    """
    Liste de toutes les commandes
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.select_related('table', 'waiter').prefetch_related('items').all()
        
        # Recherche
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(customer_name__icontains=search_query) |
                Q(table__number__icontains=search_query)
            )
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtre par type
        order_type = self.request.GET.get('order_type')
        if order_type:
            queryset = queryset.filter(order_type=order_type)
        
        # Filtre par date
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = OrderSearchForm(self.request.GET)
        
        # Statistiques
        context['total_orders'] = Order.objects.count()
        context['pending_orders'] = Order.objects.filter(status='pending').count()
        context['preparing_orders'] = Order.objects.filter(status='preparing').count()
        context['ready_orders'] = Order.objects.filter(status='ready').count()
        
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Détails d'une commande
    """
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_modify'] = self.object.can_be_modified()
        context['can_cancel'] = self.object.can_be_cancelled()
        return context


class OrderCreateView(LoginRequiredMixin, WaiterRequiredMixin, CreateView):
    """
    Créer une nouvelle commande
    """
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    
    def form_valid(self, form):
        order = form.save(commit=False)
        order.waiter = self.request.user
        order.save()
        
        # Marquer la table comme occupée si commande sur place
        if order.table and order.order_type == 'dine_in':
            order.table.status = 'occupied'
            order.table.save()
        
        messages.success(self.request, f'Commande {order.order_number} créée avec succès.')
        return redirect('orders:order_add_items', pk=order.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle commande'
        return context


@login_required
def order_add_items(request, pk):
    """
    Ajouter des articles à une commande
    """
    order = get_object_or_404(Order, pk=pk)
    
    # Vérifier les permissions
    if not request.user.can_take_orders():
        messages.error(request, "Vous n'avez pas la permission de modifier cette commande.")
        return redirect('orders:order_list')
    
    if not order.can_be_modified():
        messages.error(request, "Cette commande ne peut plus être modifiée.")
        return redirect('orders:order_detail', pk=order.pk)
    
    categories = MenuItem.objects.filter(is_available=True).values_list('category', flat=True).distinct()
    categories_list = Category.objects.filter(id__in=categories, is_active=True).order_by('order')
    menu_items = MenuItem.objects.filter(is_available=True).select_related('category')
    
    context = {
        'order': order,
        'menu_items': menu_items,
        'categories_list': categories_list,
    }
    
    return render(request, 'orders/order_add_items.html', context)


@login_required
def add_item_to_order(request, pk):
    """
    Ajouter un article à une commande (AJAX)
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        
        if not order.can_be_modified():
            return JsonResponse({'error': 'Cette commande ne peut plus être modifiée'}, status=400)
        
        menu_item_id = request.POST.get('menu_item_id')
        quantity = int(request.POST.get('quantity', 1))
        notes = request.POST.get('notes', '')
        
        menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
        
        # Vérifier si l'article existe déjà dans la commande
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            menu_item=menu_item,
            notes=notes,
            defaults={'quantity': quantity, 'price': menu_item.price}
        )
        
        if not created:
            # Si l'article existe, augmenter la quantité
            order_item.quantity += quantity
            order_item.save()
        
        # Recalculer les totaux
        order.calculate_totals()
        
        return JsonResponse({
            'success': True,
            'message': f'{menu_item.name} ajouté à la commande',
            'total_items': order.get_total_items(),
            'total': str(order.total)
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def remove_item_from_order(request, pk, item_id):
    """
    Supprimer un article d'une commande (AJAX)
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        
        if not order.can_be_modified():
            return JsonResponse({'error': 'Cette commande ne peut plus être modifiée'}, status=400)
        
        order_item = get_object_or_404(OrderItem, pk=item_id, order=order)
        order_item.delete()
        
        # Recalculer les totaux
        order.calculate_totals()
        
        return JsonResponse({
            'success': True,
            'message': 'Article supprimé',
            'total_items': order.get_total_items(),
            'total': str(order.total)
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def update_item_quantity(request, pk, item_id):
    """
    Modifier la quantité d'un article (AJAX)
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        
        if not order.can_be_modified():
            return JsonResponse({'error': 'Cette commande ne peut plus être modifiée'}, status=400)
        
        order_item = get_object_or_404(OrderItem, pk=item_id, order=order)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            order_item.quantity = quantity
            order_item.save()
            
            # Recalculer les totaux
            order.calculate_totals()
            
            return JsonResponse({
                'success': True,
                'subtotal': str(order_item.get_subtotal()),
                'total': str(order.total)
            })
        else:
            return JsonResponse({'error': 'La quantité doit être supérieure à 0'}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def confirm_order(request, pk):
    """
    Confirmer une commande et l'envoyer en cuisine
    """
    order = get_object_or_404(Order, pk=pk)
    
    if not order.can_be_modified():
        messages.error(request, "Cette commande ne peut plus être modifiée.")
        return redirect('orders:order_detail', pk=order.pk)
    
    if not order.items.exists():
        messages.error(request, "Impossible de confirmer une commande vide.")
        return redirect('orders:order_add_items', pk=order.pk)
    
    order.mark_as_confirmed()
    messages.success(request, f'Commande {order.order_number} confirmée et envoyée en cuisine.')
    
    return redirect('orders:order_detail', pk=order.pk)


@login_required
def cancel_order(request, pk):
    """
    Annuler une commande
    """
    order = get_object_or_404(Order, pk=pk)
    
    if not order.can_be_cancelled():
        messages.error(request, "Cette commande ne peut plus être annulée.")
        return redirect('orders:order_detail', pk=order.pk)
    
    if request.method == 'POST':
        order.mark_as_cancelled()
        messages.success(request, f'Commande {order.order_number} annulée.')
        return redirect('orders:order_list')
    
    return render(request, 'orders/order_confirm_cancel.html', {'order': order})


# ============================================
# INTERFACE CUISINE (KDS - Kitchen Display System)
# ============================================

@login_required
def kitchen_display(request):
    """
    Affichage des commandes en cuisine
    """
    # Vérifier si l'utilisateur est cuisinier
    if not (request.user.is_chef() or request.user.is_manager() or request.user.is_admin()):
        messages.error(request, "Accès réservé au personnel de cuisine.")
        return redirect('dashboard:home')
    
    # Récupérer les commandes en préparation ou confirmées
    orders = Order.objects.filter(
        status__in=['confirmed', 'preparing']
    ).select_related('table', 'waiter').prefetch_related('items__menu_item').order_by('created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'orders/kitchen_display.html', context)


@login_required
def update_order_status(request, pk):
    """
    Mettre à jour le statut d'une commande (AJAX)
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status == 'preparing':
            order.mark_as_preparing()
        elif new_status == 'ready':
            order.mark_as_ready()
        elif new_status == 'served':
            order.mark_as_served()
        
        return JsonResponse({
            'success': True,
            'status': order.get_status_display(),
            'status_code': order.status
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


# ============================================
# FACTURATION
# ============================================

class InvoiceListView(LoginRequiredMixin, CashierRequiredMixin, ListView):
    """
    Liste de toutes les factures
    """
    model = Invoice
    template_name = 'orders/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        return Invoice.objects.select_related('order', 'cashier').order_by('-created_at')


@login_required
def create_invoice(request, order_pk):
    """
    Créer une facture pour une commande
    """
    # Vérifier les permissions
    if not (request.user.is_cashier() or request.user.is_manager() or request.user.is_admin()):
        messages.error(request, "Vous n'avez pas la permission de créer des factures.")
        return redirect('orders:order_detail', pk=order_pk)
    
    order = get_object_or_404(Order, pk=order_pk)
    
    # Vérifier si une facture existe déjà
    if hasattr(order, 'invoice'):
        messages.info(request, "Une facture existe déjà pour cette commande.")
        return redirect('orders:invoice_detail', pk=order.invoice.pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, order=order)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.order = order
            invoice.cashier = request.user
            invoice.subtotal = order.subtotal
            invoice.tax = order.tax
            invoice.discount = order.discount
            invoice.total = order.total
            invoice.save()
            
            # Calculer le rendu de monnaie
            invoice.calculate_change()
            
            # Marquer comme payée
            invoice.mark_as_paid()
            
            messages.success(request, f'Facture {invoice.invoice_number} créée avec succès.')
            return redirect('orders:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(order=order)
    
    context = {
        'form': form,
        'order': order,
    }
    
    return render(request, 'orders/invoice_form.html', context)


@login_required
def invoice_detail(request, pk):
    """
    Détails d'une facture
    """
    invoice = get_object_or_404(Invoice, pk=pk)
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'orders/invoice_detail.html', context)


@login_required
def apply_discount(request, pk):
    """
    Appliquer une remise sur une commande
    """
    order = get_object_or_404(Order, pk=pk)
    
    if not order.can_be_modified():
        messages.error(request, "Cette commande ne peut plus être modifiée.")
        return redirect('orders:order_detail', pk=order.pk)
    
    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            discount_type = form.cleaned_data['discount_type']
            discount_value = form.cleaned_data['discount_value']
            
            if discount_type == 'amount':
                order.discount = discount_value
            else:  # percentage
                order.discount = order.subtotal * (discount_value / 100)
            
            order.calculate_totals()
            messages.success(request, 'Remise appliquée avec succès.')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = DiscountForm()
    
    context = {
        'form': form,
        'order': order,
    }
    
    return render(request, 'orders/apply_discount.html', context)