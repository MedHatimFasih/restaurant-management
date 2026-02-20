from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, datetime
from decimal import Decimal
import json

from apps.orders.models import Order, OrderItem, Invoice
from apps.tables.models import Table, Reservation
from apps.menu.models import MenuItem, Category
from apps.users.models import CustomUser
from .models import DailySales, ActivityLog, SystemAlert


# ============================================
# MIXINS DE PERMISSIONS
# ============================================

class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur peut voir le dashboard
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_view_reports()
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission d'accéder au tableau de bord.")
        return redirect('orders:order_list')


# ============================================
# TABLEAU DE BORD PRINCIPAL
# ============================================

@login_required
def home(request):
    """
    Page d'accueil du tableau de bord
    """
    today = timezone.now().date()
    
    # Vérifier les permissions
    if not request.user.can_view_reports():
        # Rediriger selon le rôle
        if request.user.is_waiter():
            return redirect('orders:order_list')
        elif request.user.is_chef():
            return redirect('orders:kitchen_display')
        elif request.user.is_cashier():
            return redirect('orders:invoice_list')
        else:
            return redirect('menu:menu_list')
    
    # ========== STATISTIQUES DU JOUR ==========
    today_orders = Order.objects.filter(created_at__date=today)
    today_revenue = today_orders.filter(is_paid=True).aggregate(
        total=Sum('total')
    )['total'] or Decimal('0')
    
    today_orders_count = today_orders.count()
    pending_orders = today_orders.filter(status__in=['pending', 'confirmed']).count()
    preparing_orders = today_orders.filter(status='preparing').count()
    
    # ========== STATISTIQUES DES TABLES ==========
    total_tables = Table.objects.filter(is_active=True).count()
    occupied_tables = Table.objects.filter(status='occupied').count()
    available_tables = Table.objects.filter(status='available', is_active=True).count()
    reserved_tables = Table.objects.filter(status='reserved').count()
    
    occupation_rate = (occupied_tables / total_tables * 100) if total_tables > 0 else 0
    
    # ========== RÉSERVATIONS ==========
    today_reservations = Reservation.objects.filter(
        date=today,
        status__in=['pending', 'confirmed']
    ).count()
    
    upcoming_reservations = Reservation.objects.filter(
        date=today,
        time__gte=timezone.now().time(),
        status='confirmed'
    ).select_related('table').order_by('time')[:5]
    
    # ========== COMMANDES RÉCENTES ==========
    recent_orders = Order.objects.select_related('table', 'waiter').order_by('-created_at')[:10]
    
    # ========== PLATS LES PLUS VENDUS (AUJOURD'HUI) ==========
    top_items_today = OrderItem.objects.filter(
        order__created_at__date=today
    ).values(
        'menu_item__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_quantity')[:5]
    
    # ========== ALERTES ==========
    unread_alerts = SystemAlert.objects.filter(
        is_read=False,
        is_resolved=False
    ).order_by('-priority', '-created_at')[:5]
    
    # ========== GRAPHIQUE CA 7 DERNIERS JOURS ==========
    last_7_days = []
    revenue_7_days = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        last_7_days.append(date.strftime('%d/%m'))
        
        daily_revenue = Order.objects.filter(
            created_at__date=date,
            is_paid=True
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        revenue_7_days.append(float(daily_revenue))
    
    # ========== PANIER MOYEN ==========
    avg_order_value = today_orders.filter(is_paid=True).aggregate(
        avg=Avg('total')
    )['avg'] or Decimal('0')
    
    context = {
        # Aujourd'hui
        'today_revenue': today_revenue,
        'today_orders_count': today_orders_count,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'avg_order_value': avg_order_value,
        
        # Tables
        'total_tables': total_tables,
        'occupied_tables': occupied_tables,
        'available_tables': available_tables,
        'reserved_tables': reserved_tables,
        'occupation_rate': round(occupation_rate, 1),
        
        # Réservations
        'today_reservations': today_reservations,
        'upcoming_reservations': upcoming_reservations,
        
        # Listes
        'recent_orders': recent_orders,
        'top_items_today': top_items_today,
        'unread_alerts': unread_alerts,
        
        # Graphiques
        'chart_labels': json.dumps(last_7_days),
        'chart_data': json.dumps(revenue_7_days),
    }
    
    return render(request, 'dashboard/home.html', context)


# ============================================
# RAPPORTS ET STATISTIQUES
# ============================================

@login_required
def sales_report(request):
    """
    Rapport des ventes détaillé
    """
    if not request.user.can_view_reports():
        messages.error(request, "Vous n'avez pas accès aux rapports.")
        return redirect('dashboard:home')
    
    # Récupérer les paramètres de filtre
    period = request.GET.get('period', 'today')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    today = timezone.now().date()
    
    # Définir la période
    if period == 'today':
        date_from = today
        date_to = today
    elif period == 'yesterday':
        date_from = today - timedelta(days=1)
        date_to = date_from
    elif period == 'week':
        date_from = today - timedelta(days=7)
        date_to = today
    elif period == 'month':
        date_from = today - timedelta(days=30)
        date_to = today
    elif period == 'custom' and start_date and end_date:
        date_from = datetime.strptime(start_date, '%Y-%m-%d').date()
        date_to = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        date_from = today
        date_to = today
    
    # Filtrer les commandes
    orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    # ========== STATISTIQUES GLOBALES ==========
    total_orders = orders.count()
    paid_orders = orders.filter(is_paid=True)
    
    total_revenue = paid_orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
    total_discount = paid_orders.aggregate(total=Sum('discount'))['total'] or Decimal('0')
    total_tax = paid_orders.aggregate(total=Sum('tax'))['total'] or Decimal('0')
    
    avg_order_value = paid_orders.aggregate(avg=Avg('total'))['avg'] or Decimal('0')
    
    # ========== RÉPARTITION PAR TYPE ==========
    orders_by_type = orders.values('order_type').annotate(
        count=Count('id'),
        revenue=Sum('total')
    )
    
    # ========== RÉPARTITION PAR STATUT ==========
    orders_by_status = orders.values('status').annotate(count=Count('id'))
    
    # ========== MODES DE PAIEMENT ==========
    invoices = Invoice.objects.filter(
        order__created_at__date__gte=date_from,
        order__created_at__date__lte=date_to
    )
    
    payment_methods = invoices.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total')
    )
    
    # ========== VENTES PAR JOUR ==========
    daily_sales = orders.filter(is_paid=True).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        orders_count=Count('id'),
        revenue=Sum('total')
    ).order_by('date')
    
    # ========== TOP 10 PLATS ==========
    top_items = OrderItem.objects.filter(
        order__created_at__date__gte=date_from,
        order__created_at__date__lte=date_to
    ).values(
        'menu_item__name',
        'menu_item__price'
    ).annotate(
        quantity=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'))
    ).order_by('-quantity')[:10]
    
    # ========== VENTES PAR CATÉGORIE ==========
    sales_by_category = OrderItem.objects.filter(
        order__created_at__date__gte=date_from,
        order__created_at__date__lte=date_to
    ).values(
        'menu_item__category__name'
    ).annotate(
        quantity=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'))
    ).order_by('-revenue')
    
    context = {
        'period': period,
        'date_from': date_from,
        'date_to': date_to,
        
        # Statistiques globales
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_discount': total_discount,
        'total_tax': total_tax,
        'avg_order_value': avg_order_value,
        
        # Répartitions
        'orders_by_type': orders_by_type,
        'orders_by_status': orders_by_status,
        'payment_methods': payment_methods,
        
        # Listes
        'daily_sales': daily_sales,
        'top_items': top_items,
        'sales_by_category': sales_by_category,
    }
    
    return render(request, 'dashboard/sales_report.html', context)


@login_required
def menu_performance(request):
    """
    Rapport de performance du menu
    """
    if not request.user.can_view_reports():
        messages.error(request, "Vous n'avez pas accès aux rapports.")
        return redirect('dashboard:home')
    
    # Période (par défaut : 30 derniers jours)
    days = int(request.GET.get('days', 30))
    date_from = timezone.now().date() - timedelta(days=days)
    
    # ========== STATISTIQUES PAR PLAT ==========
    menu_stats = OrderItem.objects.filter(
        order__created_at__date__gte=date_from
    ).values(
        'menu_item__id',
        'menu_item__name',
        'menu_item__category__name',
        'menu_item__price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_revenue')
    
    # ========== PLATS NON VENDUS ==========
    sold_item_ids = OrderItem.objects.filter(
        order__created_at__date__gte=date_from
    ).values_list('menu_item_id', flat=True).distinct()
    
    unsold_items = MenuItem.objects.filter(
        is_available=True
    ).exclude(id__in=sold_item_ids)
    
    # ========== STATISTIQUES PAR CATÉGORIE ==========
    category_stats = OrderItem.objects.filter(
        order__created_at__date__gte=date_from
    ).values(
        'menu_item__category__name'
    ).annotate(
        items_count=Count('menu_item__id', distinct=True),
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_revenue')
    
    context = {
        'days': days,
        'date_from': date_from,
        'menu_stats': menu_stats,
        'unsold_items': unsold_items,
        'category_stats': category_stats,
    }
    
    return render(request, 'dashboard/menu_performance.html', context)


@login_required
def staff_performance(request):
    """
    Rapport de performance du personnel
    """
    if not request.user.can_view_reports():
        messages.error(request, "Vous n'avez pas accès aux rapports.")
        return redirect('dashboard:home')
    
    # Période (par défaut : 30 derniers jours)
    days = int(request.GET.get('days', 30))
    date_from = timezone.now().date() - timedelta(days=days)
    
    # ========== PERFORMANCE DES SERVEURS ==========
    waiters_stats = Order.objects.filter(
        created_at__date__gte=date_from,
        waiter__isnull=False
    ).values(
        'waiter__id',
        'waiter__first_name',
        'waiter__last_name'
    ).annotate(
        orders_count=Count('id'),
        total_revenue=Sum('total', filter=Q(is_paid=True)),
        avg_order_value=Avg('total', filter=Q(is_paid=True))
    ).order_by('-total_revenue')
    
    # ========== PERFORMANCE DES CAISSIERS ==========
    cashiers_stats = Invoice.objects.filter(
        created_at__date__gte=date_from,
        cashier__isnull=False
    ).values(
        'cashier__id',
        'cashier__first_name',
        'cashier__last_name'
    ).annotate(
        invoices_count=Count('id'),
        total_processed=Sum('total')
    ).order_by('-total_processed')
    
    context = {
        'days': days,
        'date_from': date_from,
        'waiters_stats': waiters_stats,
        'cashiers_stats': cashiers_stats,
    }
    
    return render(request, 'dashboard/staff_performance.html', context)


# ============================================
# ALERTES SYSTÈME
# ============================================

class AlertListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    """
    Liste de toutes les alertes
    """
    model = SystemAlert
    template_name = 'dashboard/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SystemAlert.objects.all()
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status == 'unresolved':
            queryset = queryset.filter(is_resolved=False)
        elif status == 'resolved':
            queryset = queryset.filter(is_resolved=True)
        
        # Filtre par priorité
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-priority', '-created_at')


@login_required
def mark_alert_read(request, pk):
    """
    Marquer une alerte comme lue (AJAX)
    """
    if request.method == 'POST':
        alert = SystemAlert.objects.get(pk=pk)
        alert.mark_as_read()
        
        return JsonResponse({
            'success': True,
            'message': 'Alerte marquée comme lue'
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def resolve_alert(request, pk):
    """
    Résoudre une alerte
    """
    if not request.user.can_view_reports():
        messages.error(request, "Vous n'avez pas la permission.")
        return redirect('dashboard:home')
    
    alert = SystemAlert.objects.get(pk=pk)
    alert.resolve(user=request.user)
    
    messages.success(request, 'Alerte résolue avec succès.')
    return redirect('dashboard:alert_list')


# ============================================
# JOURNAL D'ACTIVITÉ
# ============================================

class ActivityLogListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    """
    Journal d'activité du système
    """
    model = ActivityLog
    template_name = 'dashboard/activity_log.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ActivityLog.objects.select_related('user').all()
        
        # Filtre par action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filtre par utilisateur
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtre par date
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(created_at__date=date)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = CustomUser.objects.filter(is_active=True)
        context['actions'] = ActivityLog.ACTION_CHOICES
        return context


# ============================================
# EXPORT DE DONNÉES
# ============================================

@login_required
def export_sales_csv(request):
    """
    Exporter les ventes en CSV
    """
    if not request.user.can_view_reports():
        messages.error(request, "Vous n'avez pas la permission.")
        return redirect('dashboard:home')
    
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ventes.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Numéro', 'Type', 'Statut', 'Total', 'Payée'])
    
    orders = Order.objects.all().order_by('-created_at')
    
    for order in orders:
        writer.writerow([
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.order_number,
            order.get_order_type_display(),
            order.get_status_display(),
            order.total,
            'Oui' if order.is_paid else 'Non'
        ])
    
    return response


# ============================================
# API POUR GRAPHIQUES (AJAX)
# ============================================

@login_required
def chart_revenue_api(request):
    """
    API pour les données du graphique de revenus
    """
    days = int(request.GET.get('days', 7))
    today = timezone.now().date()
    
    data = []
    labels = []
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        labels.append(date.strftime('%d/%m'))
        
        revenue = Order.objects.filter(
            created_at__date=date,
            is_paid=True
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        data.append(float(revenue))
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })


@login_required
def chart_orders_api(request):
    """
    API pour les données du graphique de commandes
    """
    days = int(request.GET.get('days', 7))
    today = timezone.now().date()
    
    data = []
    labels = []
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        labels.append(date.strftime('%d/%m'))
        
        count = Order.objects.filter(created_at__date=date).count()
        data.append(count)
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })