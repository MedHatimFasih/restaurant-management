from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé avec gestion des rôles
    """
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('manager', 'Gérant'),
        ('waiter', 'Serveur'),
        ('chef', 'Cuisinier'),
        ('cashier', 'Caissier'),
    ]

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email"
    )
    
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Téléphone"
    )
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='waiter',
        verbose_name="Rôle"
    )
    
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
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
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == 'admin'
    
    def is_manager(self):
        """Vérifie si l'utilisateur est gérant"""
        return self.role == 'manager'
    
    def is_waiter(self):
        """Vérifie si l'utilisateur est serveur"""
        return self.role == 'waiter'
    
    def is_chef(self):
        """Vérifie si l'utilisateur est cuisinier"""
        return self.role == 'chef'
    
    def is_cashier(self):
        """Vérifie si l'utilisateur est caissier"""
        return self.role == 'cashier'
    
    def can_manage_users(self):
        """Vérifie si l'utilisateur peut gérer d'autres utilisateurs"""
        return self.role in ['admin', 'manager']
    
    def can_manage_menu(self):
        """Vérifie si l'utilisateur peut gérer le menu"""
        return self.role in ['admin', 'manager', 'chef']
    
    def can_take_orders(self):
        """Vérifie si l'utilisateur peut prendre des commandes"""
        return self.role in ['waiter', 'manager']
    
    def can_view_reports(self):
        """Vérifie si l'utilisateur peut voir les rapports"""
        return self.role in ['admin', 'manager']