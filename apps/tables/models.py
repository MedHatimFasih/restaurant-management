from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Table(models.Model):
    """
    Modèle pour les tables du restaurant
    """
    STATUS_CHOICES = [
        ('available', 'Libre'),
        ('occupied', 'Occupée'),
        ('reserved', 'Réservée'),
        ('cleaning', 'En nettoyage'),
        ('out_of_service', 'Hors service'),
    ]
    
    ZONE_CHOICES = [
        ('main_hall', 'Salle principale'),
        ('terrace', 'Terrasse'),
        ('private_room', 'Salon privé'),
        ('bar', 'Bar'),
        ('vip', 'VIP'),
    ]
    
    number = models.PositiveIntegerField(
        unique=True,
        verbose_name="Numéro de table"
    )
    
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name="Capacité (personnes)"
    )
    
    zone = models.CharField(
        max_length=20,
        choices=ZONE_CHOICES,
        default='main_hall',
        verbose_name="Zone"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name="Statut"
    )
    
    position_x = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Position X",
        help_text="Position horizontale sur le plan de salle"
    )
    
    position_y = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Position Y",
        help_text="Position verticale sur le plan de salle"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Ex: Près de la fenêtre, vue sur le jardin"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        ordering = ['zone', 'number']
    
    def __str__(self):
        return f"Table {self.number} ({self.capacity} pers.) - {self.get_zone_display()}"
    
    def is_available(self):
        """Vérifie si la table est disponible"""
        return self.status == 'available' and self.is_active
    
    def is_occupied(self):
        """Vérifie si la table est occupée"""
        return self.status == 'occupied'
    
    def is_reserved(self):
        """Vérifie si la table est réservée"""
        return self.status == 'reserved'
    
    def get_current_order(self):
        """Retourne la commande en cours pour cette table"""
        from apps.orders.models import Order
        return Order.objects.filter(
            table=self,
            status__in=['pending', 'confirmed', 'preparing', 'ready']
        ).first()
    
    def set_occupied(self):
        """Marquer la table comme occupée"""
        if self.is_available():
            self.status = 'occupied'
            self.save()
            return True
        return False
    
    def set_available(self):
        """Marquer la table comme libre"""
        self.status = 'available'
        self.save()
    
    def set_reserved(self):
        """Marquer la table comme réservée"""
        if self.is_available():
            self.status = 'reserved'
            self.save()
            return True
        return False
    
    def set_cleaning(self):
        """Marquer la table comme en nettoyage"""
        self.status = 'cleaning'
        self.save()
    
    def get_status_color(self):
        """Retourne la couleur associée au statut"""
        colors = {
            'available': 'success',
            'occupied': 'danger',
            'reserved': 'warning',
            'cleaning': 'info',
            'out_of_service': 'secondary',
        }
        return colors.get(self.status, 'secondary')
    
    def get_status_icon(self):
        """Retourne l'icône associée au statut"""
        icons = {
            'available': 'bi-check-circle',
            'occupied': 'bi-person-fill',
            'reserved': 'bi-calendar-check',
            'cleaning': 'bi-tools',
            'out_of_service': 'bi-x-circle',
        }
        return icons.get(self.status, 'bi-question-circle')


class TableMerge(models.Model):
    """
    Modèle pour la fusion temporaire de tables
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nom de la fusion"
    )
    
    tables = models.ManyToManyField(
        Table,
        related_name='merges',
        verbose_name="Tables fusionnées"
    )
    
    total_capacity = models.PositiveIntegerField(
        default=0,
        verbose_name="Capacité totale"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        verbose_name="Date de création"
    )
    
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Créée par"
    )
    
    class Meta:
        verbose_name = "Fusion de tables"
        verbose_name_plural = "Fusions de tables"
        ordering = ['-created_at']
    
    def __str__(self):
        table_numbers = ', '.join(str(t.number) for t in self.tables.all())
        return f"Fusion: Tables {table_numbers}"
    
    def save(self, *args, **kwargs):
        """Calculer la capacité totale"""
        super().save(*args, **kwargs)
        if self.tables.exists():
            self.total_capacity = sum(table.capacity for table in self.tables.all())
            super().save(update_fields=['total_capacity'])
    
    def activate(self):
        """Activer la fusion et marquer les tables comme occupées"""
        self.is_active = True
        self.save()
        
        for table in self.tables.all():
            table.status = 'occupied'
            table.save()
    
    def deactivate(self):
        """Désactiver la fusion et libérer les tables"""
        self.is_active = False
        self.save()
        
        for table in self.tables.all():
            table.status = 'available'
            table.save()


class Reservation(models.Model):
    """
    Modèle pour les réservations de tables
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
        ('completed', 'Terminée'),
        ('no_show', 'Non présenté'),
    ]
    
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="Table"
    )
    
    customer_name = models.CharField(
        max_length=200,
        verbose_name="Nom du client"
    )
    
    customer_phone = models.CharField(
        max_length=15,
        verbose_name="Téléphone"
    )
    
    customer_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email"
    )
    
    num_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre de personnes"
    )
    
    date = models.DateField(
        verbose_name="Date de réservation"
    )
    
    time = models.TimeField(
        verbose_name="Heure de réservation"
    )
    
    duration_minutes = models.PositiveIntegerField(
        default=120,
        verbose_name="Durée estimée (minutes)"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Allergies, occasions spéciales, etc."
    )
    
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reservations_created',
        verbose_name="Créée par"
    )
    
    confirmed_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations_confirmed',
        verbose_name="Confirmée par"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        verbose_name="Date de modification"
    )
    
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Confirmée le"
    )
    
    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['date', 'time']
        unique_together = ['table', 'date', 'time']
    
    def __str__(self):
        return f"Réservation - Table {self.table.number} - {self.customer_name} - {self.date} {self.time}"
    
    def is_past(self):
        """Vérifie si la réservation est passée"""
        from django.utils import timezone
        import datetime
        
        reservation_datetime = datetime.datetime.combine(self.date, self.time)
        if timezone.is_aware(timezone.now()):
            reservation_datetime = timezone.make_aware(reservation_datetime)
        return reservation_datetime < timezone.now()
    
    def can_be_confirmed(self):
        """Vérifie si la réservation peut être confirmée"""
        return self.status == 'pending'
    
    def can_be_cancelled(self):
        """Vérifie si la réservation peut être annulée"""
        return self.status in ['pending', 'confirmed'] and not self.is_past()
    
    def confirm(self, user=None):
        """Confirmer la réservation"""
        if self.can_be_confirmed():
            from django.utils import timezone
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            if user:
                self.confirmed_by = user
            
            # Marquer la table comme réservée
            self.table.set_reserved()
            
            self.save()
            return True
        return False
    
    def cancel(self):
        """Annuler la réservation"""
        if self.can_be_cancelled():
            self.status = 'cancelled'
            
            # Libérer la table si elle était réservée
            if self.table.is_reserved():
                self.table.set_available()
            
            self.save()
            return True
        return False
    
    def mark_as_no_show(self):
        """Marquer comme non présenté"""
        if self.status == 'confirmed' and self.is_past():
            self.status = 'no_show'
            
            # Libérer la table
            if self.table.is_reserved():
                self.table.set_available()
            
            self.save()
            return True
        return False
    
    def mark_as_completed(self):
        """Marquer comme terminée"""
        if self.status == 'confirmed':
            self.status = 'completed'
            self.save()
            return True
        return False
    
    def get_status_color(self):
        """Retourne la couleur associée au statut"""
        colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger',
            'completed': 'info',
            'no_show': 'secondary',
        }
        return colors.get(self.status, 'secondary')