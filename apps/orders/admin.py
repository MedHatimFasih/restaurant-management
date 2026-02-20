from django.contrib import admin
from .models import Order, OrderItem, Invoice


class OrderItemInline(admin.TabularInline):
    """
    Inline pour afficher les articles dans l'admin des commandes
    """
    model = OrderItem
    extra = 0
    readonly_fields = ('get_subtotal',)
    fields = ('menu_item', 'quantity', 'price', 'notes', 'status', 'get_subtotal')
    
    def get_subtotal(self, obj):
        return f"{obj.get_subtotal()} MAD"
    get_subtotal.short_description = 'Sous-total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les commandes
    """
    list_display = ('order_number', 'table', 'waiter', 'order_type', 'status', 'total', 'is_paid', 'created_at')
    list_filter = ('status', 'order_type', 'is_paid', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone')
    readonly_fields = ('order_number', 'subtotal', 'tax', 'total', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('order_number', 'table', 'waiter', 'order_type', 'status')
        }),
        ('Client', {
            'fields': ('customer_name', 'customer_phone', 'delivery_address')
        }),
        ('Montants', {
            'fields': ('subtotal', 'tax', 'discount', 'total', 'is_paid')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'served_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les articles de commande
    """
    list_display = ('order', 'menu_item', 'quantity', 'price', 'status', 'get_subtotal')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'menu_item__name')
    readonly_fields = ('get_subtotal',)
    
    def get_subtotal(self, obj):
        return f"{obj.get_subtotal()} MAD"
    get_subtotal.short_description = 'Sous-total'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les factures
    """
    list_display = ('invoice_number', 'order', 'payment_method', 'total', 'is_paid', 'cashier', 'created_at')
    list_filter = ('payment_method', 'is_paid', 'created_at')
    search_fields = ('invoice_number', 'order__order_number')
    readonly_fields = ('invoice_number', 'subtotal', 'tax', 'total', 'change', 'created_at', 'paid_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('invoice_number', 'order', 'payment_method')
        }),
        ('Montants', {
            'fields': ('subtotal', 'tax', 'discount', 'total', 'amount_paid', 'change')
        }),
        ('Paiement', {
            'fields': ('is_paid', 'cashier', 'notes')
        }),
        ('Dates', {
            'fields': ('created_at', 'paid_at')
        }),
    )