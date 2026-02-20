from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.users.models import CustomUser
from apps.tables.models import Table
from apps.menu.models import MenuItem


class Order(models.Model):
    """
    Modèle pour les commandes
    """
    TYPE_CHOICES = [
        ('dine_in', 'Sur place'),
        ('takeaway', 'À emporter'),
        ('delivery', 'Livraison'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('preparing', 'En préparation'),
        ('ready', 'Prête'),
        ('served', 'Servie'),
        ('cancelled', 'Annulée'),
    ]
    
    order_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Numéro de commande"
    )
    
    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Table"
    )
    
    waiter = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name="Serveur"
    )
    
    order_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='dine_in',
        verbose_name="Type de commande"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nom du client",
        help_text="Pour les commandes à emporter ou en livraison"
    )
    
    customer_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Téléphone du client"
    )
    
    delivery_address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Adresse de livraison"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Sous-total"
    )
    
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Taxe (TVA)"
    )
    
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Remise"
    )
    
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total"
    )
    
    is_paid = models.BooleanField(
        default=False,
        verbose_name="Payée"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Confirmée le"
    )
    
    served_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Servie le"
    )
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']
    
    def __str__(self):
        if self.table:
            return f"Commande #{self.order_number} - Table {self.table.number}"
        return f"Commande #{self.order_number} - {self.get_order_type_display()}"
    
    def save(self, *args, **kwargs):
        """Générer automatiquement le numéro de commande"""
        if not self.order_number:
            # Format: ORD-YYYYMMDD-XXXX
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = Order.objects.filter(created_at__date=today.date()).count() + 1
            self.order_number = f"ORD-{date_str}-{count:04d}"
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculer les totaux de la commande"""
        # Calculer le sous-total
        self.subtotal = sum(item.get_subtotal() for item in self.items.all())
        
        # Calculer la taxe (TVA 20%)
        self.tax = self.subtotal * 0.20
        
        # Calculer le total
        self.total = self.subtotal + self.tax - self.discount
        
        self.save()
    
    def get_total_items(self):
        """Retourne le nombre total d'articles"""
        return sum(item.quantity for item in self.items.all())
    
    def get_preparation_time(self):
        """Calcule le temps de préparation estimé"""
        if self.items.exists():
            return max(item.menu_item.prep_time for item in self.items.all())
        return 0
    
    def can_be_modified(self):
        """Vérifie si la commande peut être modifiée"""
        return self.status in ['pending', 'confirmed']
    
    def can_be_cancelled(self):
        """Vérifie si la commande peut être annulée"""
        return self.status not in ['served', 'cancelled']
    
    def mark_as_confirmed(self):
        """Marquer la commande comme confirmée"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            self.save()
    
    def mark_as_preparing(self):
        """Marquer la commande comme en préparation"""
        if self.status in ['pending', 'confirmed']:
            self.status = 'preparing'
            self.save()
    
    def mark_as_ready(self):
        """Marquer la commande comme prête"""
        if self.status == 'preparing':
            self.status = 'ready'
            self.save()
    
    def mark_as_served(self):
        """Marquer la commande comme servie"""
        if self.status in ['ready', 'preparing']:
            self.status = 'served'
            self.served_at = timezone.now()
            self.save()
    
    def mark_as_cancelled(self):
        """Annuler la commande"""
        if self.can_be_cancelled():
            self.status = 'cancelled'
            self.save()
            
            # Libérer la table si elle était occupée
            if self.table and self.table.status == 'occupied':
                self.table.status = 'available'
                self.table.save()


class OrderItem(models.Model):
    """
    Modèle pour les articles d'une commande
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('preparing', 'En préparation'),
        ('ready', 'Prêt'),
        ('served', 'Servi'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Commande"
    )
    
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        verbose_name="Plat"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Quantité"
    )
    
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix unitaire"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Ex: Sans sauce, bien cuit, etc."
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
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
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"
    
    def save(self, *args, **kwargs):
        """Enregistrer le prix au moment de la commande"""
        if not self.price:
            self.price = self.menu_item.price
        super().save(*args, **kwargs)
    
    def get_subtotal(self):
        """Calculer le sous-total de l'article"""
        return self.quantity * self.price
    
    def mark_as_preparing(self):
        """Marquer l'article comme en préparation"""
        self.status = 'preparing'
        self.save()
    
    def mark_as_ready(self):
        """Marquer l'article comme prêt"""
        self.status = 'ready'
        self.save()
    
    def mark_as_served(self):
        """Marquer l'article comme servi"""
        self.status = 'served'
        self.save()


class Invoice(models.Model):
    """
    Modèle pour les factures
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Espèces'),
        ('card', 'Carte bancaire'),
        ('check', 'Chèque'),
        ('voucher', 'Ticket restaurant'),
        ('mobile', 'Paiement mobile'),
    ]
    
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Numéro de facture"
    )
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invoice',
        verbose_name="Commande"
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Sous-total"
    )
    
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Taxe (TVA)"
    )
    
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Remise"
    )
    
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Total"
    )
    
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Mode de paiement"
    )
    
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant payé"
    )
    
    change = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Rendu de monnaie"
    )
    
    cashier = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invoices',
        verbose_name="Caissier"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    
    is_paid = models.BooleanField(
        default=False,
        verbose_name="Payée"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Payée le"
    )
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Facture #{self.invoice_number}"
    
    def save(self, *args, **kwargs):
        """Générer automatiquement le numéro de facture"""
        if not self.invoice_number:
            # Format: INV-YYYYMMDD-XXXX
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = Invoice.objects.filter(created_at__date=today.date()).count() + 1
            self.invoice_number = f"INV-{date_str}-{count:04d}"
        
        super().save(*args, **kwargs)
    
    def calculate_change(self):
        """Calculer le rendu de monnaie"""
        if self.amount_paid > self.total:
            self.change = self.amount_paid - self.total
        else:
            self.change = 0
        self.save()
    
    def mark_as_paid(self):
        """Marquer la facture comme payée"""
        self.is_paid = True
        self.paid_at = timezone.now()
        self.order.is_paid = True
        self.order.save()
        self.save()