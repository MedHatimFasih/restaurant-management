from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal

from apps.users.models import CustomUser
from apps.menu.models import Category, MenuItem
from apps.tables.models import Table
from .models import Order, OrderItem, Invoice


class OrderModelTest(TestCase):
    """
    Tests du modèle Order
    """
    
    def setUp(self):
        self.waiter = CustomUser.objects.create_user(
            username='waiter',
            password='test123',
            role='waiter'
        )
        
        self.table = Table.objects.create(
            number=1,
            capacity=4,
            zone='Salle principale'
        )
        
        self.order = Order.objects.create(
            table=self.table,
            waiter=self.waiter,
            order_type='dine_in'
        )
    
    def test_order_creation(self):
        """Test de création de commande"""
        self.assertIsNotNone(self.order.order_number)
        self.assertTrue(self.order.order_number.startswith('ORD-'))
        self.assertEqual(self.order.status, 'pending')
    
    def test_order_str(self):
        """Test de la représentation string"""
        self.assertIn(self.order.order_number, str(self.order))


class OrderItemModelTest(TestCase):
    """
    Tests du modèle OrderItem
    """
    
    def setUp(self):
        waiter = CustomUser.objects.create_user(
            username='waiter',
            password='test123',
            role='waiter'
        )
        
        table = Table.objects.create(number=1, capacity=4)
        
        self.order = Order.objects.create(
            table=table,
            waiter=waiter
        )
        
        category = Category.objects.create(name='Plats')
        
        self.menu_item = MenuItem.objects.create(
            name='Couscous',
            description='Délicieux couscous',
            price=Decimal('80.00'),
            category=category
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.menu_item,
            quantity=2
        )
    
    def test_orderitem_creation(self):
        """Test de création d'article de commande"""
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.price, Decimal('80.00'))
    
    def test_get_subtotal(self):
        """Test du calcul du sous-total"""
        self.assertEqual(self.order_item.get_subtotal(), Decimal('160.00'))


class OrderViewsTest(TestCase):
    """
    Tests des vues
    """
    
    def setUp(self):
        self.client = Client()
        
        self.waiter = CustomUser.objects.create_user(
            username='waiter',
            password='test123',
            role='waiter'
        )
        
        self.cashier = CustomUser.objects.create_user(
            username='cashier',
            password='test123',
            role='cashier'
        )
    
    def test_order_list_requires_login(self):
        """Test que la liste des commandes nécessite une connexion"""
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_order_list_waiter_access(self):
        """Test que le serveur peut accéder à la liste des commandes"""
        self.client.login(username='waiter', password='test123')
        response = self.client.get(reverse('orders:order_list'))
        self.assertEqual(response.status_code, 200)