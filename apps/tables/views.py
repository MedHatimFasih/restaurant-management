from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone

from .models import Table, TableMerge, Reservation
from .forms import (
    TableForm, TableSearchForm, TableMergeForm,
    ReservationForm, ReservationSearchForm, QuickReservationForm
)


# ============================================
# MIXINS DE PERMISSIONS
# ============================================

class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur peut gérer les tables
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_manager() or 
            self.request.user.is_admin()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission de gérer les tables.")
        return redirect('tables:table_list')


# ============================================
# VUES POUR LES TABLES
# ============================================

class TableListView(LoginRequiredMixin, ListView):
    """
    Liste de toutes les tables
    """
    model = Table
    template_name = 'tables/table_list.html'
    context_object_name = 'tables'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Table.objects.all()
        
        # Recherche
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(number__icontains=search_query)
        
        # Filtre par zone
        zone = self.request.GET.get('zone')
        if zone:
            queryset = queryset.filter(zone=zone)
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtre par capacité minimale
        min_capacity = self.request.GET.get('min_capacity')
        if min_capacity:
            queryset = queryset.filter(capacity__gte=min_capacity)
        
        return queryset.order_by('zone', 'number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TableSearchForm(self.request.GET)
        
        # Statistiques
        context['total_tables'] = Table.objects.filter(is_active=True).count()
        context['available_tables'] = Table.objects.filter(status='available', is_active=True).count()
        context['occupied_tables'] = Table.objects.filter(status='occupied').count()
        context['reserved_tables'] = Table.objects.filter(status='reserved').count()
        
        return context


class TableDetailView(LoginRequiredMixin, DetailView):
    """
    Détails d'une table
    """
    model = Table
    template_name = 'tables/table_detail.html'
    context_object_name = 'table'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Commande en cours
        context['current_order'] = self.object.get_current_order()
        
        # Réservations futures
        context['future_reservations'] = self.object.reservations.filter(
            date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).order_by('date', 'time')[:5]
        
        return context


class TableCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    """
    Créer une nouvelle table
    """
    model = Table
    form_class = TableForm
    template_name = 'tables/table_form.html'
    success_url = reverse_lazy('tables:table_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Table {form.instance.number} créée avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter une table'
        return context


class TableUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    """
    Modifier une table
    """
    model = Table
    form_class = TableForm
    template_name = 'tables/table_form.html'
    success_url = reverse_lazy('tables:table_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Table {form.instance.number} modifiée avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier la table'
        return context


class TableDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    """
    Supprimer une table
    """
    model = Table
    template_name = 'tables/table_confirm_delete.html'
    success_url = reverse_lazy('tables:table_list')
    
    def delete(self, request, *args, **kwargs):
        table = self.get_object()
        
        # Vérifier si la table est occupée
        if table.is_occupied():
            messages.error(request, f'Impossible de supprimer la table {table.number}. Elle est actuellement occupée.')
            return redirect('tables:table_list')
        
        messages.success(request, f'Table {table.number} supprimée avec succès.')
        return super().delete(request, *args, **kwargs)


@login_required
def floor_plan(request):
    """
    Plan de salle interactif
    """
    tables = Table.objects.filter(is_active=True).select_related()
    
    # Organiser par zone
    tables_by_zone = {}
    for table in tables:
        zone = table.get_zone_display()
        if zone not in tables_by_zone:
            tables_by_zone[zone] = []
        tables_by_zone[zone].append(table)
    
    context = {
        'tables': tables,
        'tables_by_zone': tables_by_zone,
    }
    
    return render(request, 'tables/floor_plan.html', context)


@login_required
def change_table_status(request, pk):
    """
    Changer le statut d'une table (AJAX)
    """
    if request.method == 'POST':
        table = get_object_or_404(Table, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Table.STATUS_CHOICES):
            old_status = table.get_status_display()
            table.status = new_status
            table.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Table {table.number}: {old_status} → {table.get_status_display()}',
                'status': table.status,
                'status_display': table.get_status_display(),
                'status_color': table.get_status_color()
            })
        
        return JsonResponse({'error': 'Statut invalide'}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def toggle_table_status(request, pk):
    """
    Bascule le statut d'une table entre 'available' et 'occupied'
    """
    table = get_object_or_404(Table, pk=pk)
    
    if table.status == 'available':
        table.status = 'occupied'
        messages.success(request, f'Table {table.number} est maintenant occupée.')
    else:
        table.status = 'available'
        messages.success(request, f'Table {table.number} est maintenant libre.')
    
    table.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'tables:table_list'))


# ============================================
# VUES POUR LES FUSIONS DE TABLES
# ============================================

class TableMergeListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    """
    Liste des fusions de tables
    """
    model = TableMerge
    template_name = 'tables/merge_list.html'
    context_object_name = 'merges'
    
    def get_queryset(self):
        return TableMerge.objects.filter(is_active=True).prefetch_related('tables')


class TableMergeCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    """
    Créer une fusion de tables
    """
    model = TableMerge
    form_class = TableMergeForm
    template_name = 'tables/merge_form.html'
    success_url = reverse_lazy('tables:merge_list')
    
    def form_valid(self, form):
        merge = form.save(commit=False)
        merge.created_by = self.request.user
        merge.save()
        form.save_m2m()  # Sauvegarder les relations ManyToMany
        
        # Activer la fusion
        merge.activate()
        
        messages.success(self.request, f'Fusion "{merge.name}" créée avec succès.')
        return redirect(self.success_url)


@login_required
def deactivate_merge(request, pk):
    """
    Désactiver une fusion de tables
    """
    if not (request.user.is_manager() or request.user.is_admin()):
        messages.error(request, "Vous n'avez pas la permission.")
        return redirect('tables:merge_list')
    
    merge = get_object_or_404(TableMerge, pk=pk)
    merge.deactivate()
    
    messages.success(request, f'Fusion "{merge.name}" désactivée. Les tables sont maintenant libres.')
    return redirect('tables:merge_list')


# ============================================
# VUES POUR LES RÉSERVATIONS
# ============================================

class ReservationListView(LoginRequiredMixin, ListView):
    """
    Liste de toutes les réservations
    """
    model = Reservation
    template_name = 'tables/reservation_list.html'
    context_object_name = 'reservations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Reservation.objects.select_related('table', 'created_by').all()
        
        # Recherche
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(customer_name__icontains=search_query) |
                Q(customer_phone__icontains=search_query) |
                Q(customer_email__icontains=search_query)
            )
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtre par date
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Filtre par table
        table_id = self.request.GET.get('table')
        if table_id:
            queryset = queryset.filter(table_id=table_id)
        
        return queryset.order_by('date', 'time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ReservationSearchForm(self.request.GET)
        
        # Statistiques
        today = timezone.now().date()
        context['today_reservations'] = Reservation.objects.filter(
            date=today,
            status__in=['pending', 'confirmed']
        ).count()
        context['pending_reservations'] = Reservation.objects.filter(status='pending').count()
        
        return context


class ReservationDetailView(LoginRequiredMixin, DetailView):
    """
    Détails d'une réservation
    """
    model = Reservation
    template_name = 'tables/reservation_detail.html'
    context_object_name = 'reservation'


class ReservationCreateView(LoginRequiredMixin, CreateView):
    """
    Créer une nouvelle réservation
    """
    model = Reservation
    form_class = ReservationForm
    template_name = 'tables/reservation_form.html'
    success_url = reverse_lazy('tables:reservation_list')
    
    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.created_by = self.request.user
        reservation.save()
        
        messages.success(
            self.request,
            f'Réservation créée pour {reservation.customer_name} - '
            f'Table {reservation.table.number} le {reservation.date} à {reservation.time}'
        )
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle réservation'
        return context


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    """
    Modifier une réservation
    """
    model = Reservation
    form_class = ReservationForm
    template_name = 'tables/reservation_form.html'
    success_url = reverse_lazy('tables:reservation_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Réservation modifiée avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier la réservation'
        return context


@login_required
def confirm_reservation(request, pk):
    """
    Confirmer une réservation
    """
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if reservation.confirm(user=request.user):
        messages.success(request, f'Réservation confirmée pour {reservation.customer_name}.')
    else:
        messages.error(request, 'Impossible de confirmer cette réservation.')
    
    return redirect('tables:reservation_detail', pk=pk)


@login_required
def cancel_reservation(request, pk):
    """
    Annuler une réservation
    """
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'POST':
        if reservation.cancel():
            messages.success(request, f'Réservation annulée pour {reservation.customer_name}.')
            return redirect('tables:reservation_list')
        else:
            messages.error(request, 'Impossible d\'annuler cette réservation.')
    
    return render(request, 'tables/reservation_confirm_cancel.html', {'reservation': reservation})


@login_required
def calendar_view(request):
    """
    Calendrier des réservations
    """
    # Récupérer toutes les réservations futures
    reservations = Reservation.objects.filter(
        date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).select_related('table').order_by('date', 'time')
    
    # Organiser par date
    reservations_by_date = {}
    for reservation in reservations:
        date_str = reservation.date.strftime('%Y-%m-%d')
        if date_str not in reservations_by_date:
            reservations_by_date[date_str] = []
        reservations_by_date[date_str].append(reservation)
    
    context = {
        'reservations': reservations,
        'reservations_by_date': reservations_by_date,
    }
    
    return render(request, 'tables/calendar.html', context)