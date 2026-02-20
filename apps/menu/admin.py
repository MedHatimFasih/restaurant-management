from django.contrib import admin
from .models import Category, MenuItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les catégories
    """
    list_display = ('name', 'order', 'is_active', 'get_items_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    list_editable = ('order', 'is_active')
    
    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Nombre de plats'


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """
    Configuration admin pour les plats
    """
    list_display = ('name', 'category', 'price', 'is_available', 'prep_time', 'created_at')
    list_filter = ('category', 'is_available', 'is_vegetarian', 'is_vegan', 'is_spicy', 'created_at')
    search_fields = ('name', 'description', 'allergens')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('category', 'name')
    list_editable = ('price', 'is_available')
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'slug', 'description', 'price', 'category', 'image')
        }),
        ('Disponibilité', {
            'fields': ('is_available', 'prep_time')
        }),
        ('Informations diététiques', {
            'fields': ('allergens', 'is_spicy', 'is_vegetarian', 'is_vegan', 'calories')
        }),
    )