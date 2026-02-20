from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import CustomUser
from .models import Category, MenuItem
from decimal import Decimal


class CategoryModelTest(TestCase):
    """
    Tests du modèle Category
    """
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Entrées',
            description='Délicieuses entrées',
            order=1
        )
    
    def test_category_creation(self):
        """Test de création de catégorie"""
        self.assertEqual(self.category.name, 'Entrées')
        self.assertEqual(self.category.order, 1)
        self.assertTrue(self.category.is_active)
    
    def test_category_str(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.category), 'Entrées')


class MenuItemModelTest(TestCase):
    """
    Tests du modèle MenuItem
    """
    
    def setUp(self):
        self.category = Category.objects.create(name='Plats')
        self.item = MenuItem.objects.create(
            name='Tajine Poulet',
            description='Délicieux tajine de poulet',
            price=Decimal('75.00'),
            category=self.category,
            prep_time=30
        )
    
    def test_menuitem_creation(self):
        """Test de création de plat"""
        self.assertEqual(self.item.name, 'Tajine Poulet')
        self.assertEqual(self.item.price, Decimal('75.00'))
        self.assertEqual(self.item.category, self.category)
        self.assertTrue(self.item.is_available)
    
    def test_slug_generation(self):
        """Test de génération automatique du slug"""
        self.assertEqual(self.item.slug, 'tajine-poulet')
    
    def test_menuitem_str(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.item), 'Tajine Poulet - 75.00 MAD')


class MenuViewsTest(TestCase):
    """
    Tests des vues
    """
    
    def setUp(self):
        self.client = Client()
        
        # Créer un manager
        self.manager = CustomUser.objects.create_user(
            username='manager',
            password='manager123',
            role='manager'
        )
        
        # Créer un serveur
        self.waiter = CustomUser.objects.create_user(
            username='waiter',
            password='waiter123',
            role='waiter'
        )
        
        # Créer une catégorie et un plat
        self.category = Category.objects.create(name='Plats')
        self.item = MenuItem.objects.create(
            name='Couscous',
            description='Délicieux couscous',
            price=Decimal('80.00'),
            category=self.category
        )
    
    def test_menu_list_requires_login(self):
        """Test que la liste du menu nécessite une connexion"""
        response = self.client.get(reverse('menu:menu_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_menu_list_authenticated(self):
        """Test de la liste du menu avec utilisateur connecté"""
        self.client.login(username='waiter', password='waiter123')
        response = self.client.get(reverse('menu:menu_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Couscous')
    
    def test_menu_create_manager_access(self):
        """Test que le manager peut créer un plat"""
        self.client.login(username='manager', password='manager123')
        response = self.client.get(reverse('menu:menu_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_menu_create_waiter_denied(self):
        """Test que le serveur ne peut pas créer de plat"""
        self.client.login(username='waiter', password='waiter123')
        response = self.client.get(reverse('menu:menu_create'))
        self.assertEqual(response.status_code, 302)