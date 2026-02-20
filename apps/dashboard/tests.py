from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from apps.users.models import CustomUser
from apps.orders.models import Order
from apps.tables.models import Table
from .models import DailySales, ActivityLog, SystemAlert


class DashboardViewsTest(TestCase):
    """
    Tests des vues du dashboard
    """
    
    def setUp(self):
        self.client = Client()
        
        # Créer un manager
        self.manager = CustomUser.objects.create_user(
            username='manager',
            password='test123',
            role='manager'
        )
        
        # Créer un serveur
        self.waiter = CustomUser.objects.create_user(
            username='waiter',
            password='test123',
            role='waiter'
        )
    
    def test_dashboard_requires_login(self):
        """Test que le dashboard nécessite une connexion"""
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_manager_access(self):
        """Test que le manager peut accéder au dashboard"""
        self.client.login(username='manager', password='test123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tableau de bord')
    
    def test_dashboard_waiter_redirect(self):
        """Test que le serveur est redirigé vers les commandes"""
        self.client.login(username='waiter', password='test123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)


class SystemAlertModelTest(TestCase):
    """
    Tests du modèle SystemAlert
    """
    
    def setUp(self):
        self.alert = SystemAlert.objects.create(
            alert_type='stock_low',
            priority='high',
            title='Stock faible',
            message='Le stock de tomates est faible'
        )
    
    def test_alert_creation(self):
        """Test de création d'alerte"""
        self.assertEqual(self.alert.alert_type, 'stock_low')
        self.assertEqual(self.alert.priority, 'high')
        self.assertFalse(self.alert.is_read)
        self.assertFalse(self.alert.is_resolved)
    
    def test_mark_as_read(self):
        """Test de marquage comme lu"""
        self.alert.mark_as_read()
        self.assertTrue(self.alert.is_read)
    
    def test_resolve_alert(self):
        """Test de résolution d'alerte"""
        user = CustomUser.objects.create_user(username='admin', password='test123', role='admin')
        self.alert.resolve(user=user)
        self.assertTrue(self.alert.is_resolved)
        self.assertIsNotNone(self.alert.resolved_at)
        self.assertEqual(self.alert.resolved_by, user)


class ActivityLogModelTest(TestCase):
    """
    Tests du modèle ActivityLog
    """
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='admin',
            password='test123',
            role='admin'
        )
        
        self.log = ActivityLog.objects.create(
            user=self.user,
            action='order_created',
            description='Commande #001 créée'
        )
    
    def test_log_creation(self):
        """Test de création de log"""
        self.assertEqual(self.log.user, self.user)
        self.assertEqual(self.log.action, 'order_created')
        self.assertIsNotNone(self.log.created_at)