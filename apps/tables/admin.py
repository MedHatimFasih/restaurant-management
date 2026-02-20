from django.contrib import admin
from .models import Table, TableMerge, Reservation


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les tables
    """
    list_display = ('number', 'capacity', 'zone', 'status', 'is_active', 'created_at')
    list_filter = ('zone', 'status', 'is_active', 'created_at')
    search_fields = ('number', 'description')
    ordering = ('zone', 'number')
    list_editable = ('status', 'is_active')
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('number', 'capacity', 'zone', 'status')
        }),
        ('Position', {
            'fields': ('position_x', 'position_y')
        }),
        ('Détails', {
            'fields': ('description', 'is_active')
        }),
    )


@admin.register(TableMerge)
class TableMergeAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les fusions de tables
    """
    list_display = ('name', 'total_capacity', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('tables',)
    readonly_fields = ('total_capacity', 'created_at')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les réservations
    """
    list_display = ('customer_name', 'table', 'date', 'time', 'num_guests', 'status', 'created_at')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'customer_email')
    ordering = ('-date', '-time')
    readonly_fields = ('created_at', 'updated_at', 'confirmed_at')
    
    fieldsets = (
        ('Client', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Réservation', {
            'fields': ('table', 'num_guests', 'date', 'time', 'duration_minutes')
        }),
        ('Statut', {
            'fields': ('status', 'notes')
        }),
        ('Informations système', {
            'fields': ('created_by', 'confirmed_by', 'created_at', 'updated_at', 'confirmed_at')
        }),
    )