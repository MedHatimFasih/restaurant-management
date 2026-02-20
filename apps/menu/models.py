from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify

class Category(models.Model):
    """
    Modèle pour les catégories de plats (Entrées, Plats, Desserts, etc.)
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la catégorie"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description"
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Classe d'icône Bootstrap (ex: bi-cup-hot)",
        verbose_name="Icône"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_items_count(self):
        """Retourne le nombre de plats dans cette catégorie"""
        return self.items.filter(is_available=True).count()
    
    def get_active_items(self):
        """Retourne tous les plats actifs de cette catégorie"""
        return self.items.filter(is_available=True)


class MenuItem(models.Model):
    """
    Modèle pour les plats du menu
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Nom du plat"
    )
    
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        verbose_name="Slug"
    )
    
    description = models.TextField(
        verbose_name="Description"
    )
    
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix (MAD)"
    )
    
    image = models.ImageField(
        upload_to='menu_items/',
        verbose_name="Image du plat"
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Catégorie"
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name="Disponible"
    )
    
    prep_time = models.PositiveIntegerField(
        default=15,
        help_text="Temps de préparation en minutes",
        verbose_name="Temps de préparation (min)"
    )
    
    allergens = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Ex: Gluten, Lactose, Fruits à coque",
        verbose_name="Allergènes"
    )
    
    is_spicy = models.BooleanField(
        default=False,
        verbose_name="Plat épicé"
    )
    
    is_vegetarian = models.BooleanField(
        default=False,
        verbose_name="Végétarien"
    )
    
    is_vegan = models.BooleanField(
        default=False,
        verbose_name="Végan"
    )
    
    calories = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Calories"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Plat"
        verbose_name_plural = "Plats"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.price} MAD"
    
    def save(self, *args, **kwargs):
        """Générer automatiquement le slug"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_allergens_list(self):
        """Retourne la liste des allergènes"""
        if self.allergens:
            return [allergen.strip() for allergen in self.allergens.split(',')]
        return []
    
    def get_dietary_info(self):
        """Retourne les informations diététiques"""
        info = []
        if self.is_vegetarian:
            info.append('Végétarien')
        if self.is_vegan:
            info.append('Végan')
        if self.is_spicy:
            info.append('Épicé')
        return info