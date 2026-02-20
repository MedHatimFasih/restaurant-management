from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé pour le système de gestion de restaurant
    """
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('manager', 'Manager'),
        ('chef', 'Chef de cuisine'),
        ('waiter', 'Serveur'),
        ('cashier', 'Caissier'),
    )
    
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='waiter')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        full_name = self.get_full_name()
        name = full_name if full_name else self.username
        return f"{name} ({self.get_role_display()})"

    # Méthodes de vérification de rôle
    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role == 'manager'

    def is_chef(self):
        return self.role == 'chef'

    def is_waiter(self):
        return self.role == 'waiter'

    def is_cashier(self):
        return self.role == 'cashier'

    # Méthodes de permissions
    def can_manage_users(self):
        return self.role == 'admin'

    def can_manage_menu(self):
        return self.role in ['admin', 'manager', 'chef']

    def can_take_orders(self):
        return self.role in ['admin', 'manager', 'waiter']

    def can_view_reports(self):
        return self.role in ['admin', 'manager']
