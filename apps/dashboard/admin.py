from django.contrib import admin
from .models import DailySales, ActivityLog, SystemAlert


@admin.register(DailySales)
class DailySalesAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les ventes journalières
    """
    list_display = ('date', 'total_orders', 'total_revenue', 'average_order_value', 'total_customers')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Configuration admin pour le journal d'activité
    """
    list_display = ('user', 'action', 'description', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'description', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les alertes système
    """
    list_display = ('title', 'alert_type', 'priority', 'is_read', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'priority', 'is_read', 'is_resolved', 'created_at')
    search_fields = ('title', 'message')
    ordering = ('-priority', '-created_at')
    readonly_fields = ('created_at', 'resolved_at')
    
    fieldsets = (
        ('Alerte', {
            'fields': ('alert_type', 'priority', 'title', 'message')
        }),
        ('Statut', {
            'fields': ('is_read', 'is_resolved', 'resolved_by', 'resolved_at')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )