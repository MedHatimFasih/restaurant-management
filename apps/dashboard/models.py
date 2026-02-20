from django.db import models
from django.utils import timezone
from apps.users.models import CustomUser


class DailySales(models.Model):
    """
    Modèle pour stocker les ventes journalières (pour historique et reporting)
    """
    date = models.DateField(
        unique=True,
        verbose_name="Date"
    )
    
    total_orders = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de commandes"
    )
    
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Chiffre d'affaires"
    )
    
    total_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Remises totales"
    )
    
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Panier moyen"
    )
    
    total_customers = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de clients"
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
        verbose_name = "Vente journalière"
        verbose_name_plural = "Ventes journalières"
        ordering = ['-date']
    
    def __str__(self):
        return f"Ventes du {self.date} - {self.total_revenue} MAD"


class ActivityLog(models.Model):
    """
    Modèle pour enregistrer les activités importantes du système
    """
    ACTION_CHOICES = [
        ('order_created', 'Commande créée'),
        ('order_confirmed', 'Commande confirmée'),
        ('order_cancelled', 'Commande annulée'),
        ('invoice_created', 'Facture créée'),
        ('table_status_changed', 'Statut de table modifié'),
        ('reservation_created', 'Réservation créée'),
        ('reservation_confirmed', 'Réservation confirmée'),
        ('reservation_cancelled', 'Réservation annulée'),
        ('user_login', 'Connexion utilisateur'),
        ('user_logout', 'Déconnexion utilisateur'),
        ('menu_item_added', 'Plat ajouté'),
        ('menu_item_updated', 'Plat modifié'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
        verbose_name="Utilisateur"
    )
    
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    
    description = models.TextField(
        verbose_name="Description"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        verbose_name="Date"
    )
    
    class Meta:
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activité"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.user} - {self.created_at}"


class SystemAlert(models.Model):
    """
    Modèle pour les alertes système (stocks faibles, réservations, etc.)
    """
    ALERT_TYPE_CHOICES = [
        ('stock_low', 'Stock faible'),
        ('stock_critical', 'Stock critique'),
        ('reservation_upcoming', 'Réservation à venir'),
        ('table_long_occupied', 'Table occupée longtemps'),
        ('order_delayed', 'Commande en retard'),
        ('system_error', 'Erreur système'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]
    
    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPE_CHOICES,
        verbose_name="Type d'alerte"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Priorité"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    message = models.TextField(
        verbose_name="Message"
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name="Lu"
    )
    
    is_resolved = models.BooleanField(
        default=False,
        verbose_name="Résolu"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        verbose_name="Date de création"
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Résolu le"
    )
    
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name="Résolu par"
    )
    
    class Meta:
        verbose_name = "Alerte système"
        verbose_name_plural = "Alertes système"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_priority_display()} - {self.title}"
    
    def mark_as_read(self):
        """Marquer l'alerte comme lue"""
        self.is_read = True
        self.save()
    
    def resolve(self, user=None):
        """Résoudre l'alerte"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        self.save()
    
    def get_priority_color(self):
        """Retourne la couleur Bootstrap associée à la priorité"""
        colors = {
            'low': 'info',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'danger',
        }
        return colors.get(self.priority, 'secondary')