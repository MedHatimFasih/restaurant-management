from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser


class CustomUserModelTest(TestCase):
    """
    Tests du modèle CustomUser
    """
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='0123456789',
            role='waiter'
        )
    
    def test_user_creation(self):
        """Test de création d'utilisateur"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'waiter')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_get_full_name(self):
        """Test de la méthode get_full_name"""
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_role_checks(self):
        """Test des méthodes de vérification de rôle"""
        self.assertTrue(self.user.is_waiter())
        self.assertFalse(self.user.is_admin())
        self.assertFalse(self.user.is_manager())
        self.assertFalse(self.user.is_chef())
        self.assertFalse(self.user.is_cashier())
    
    def test_permissions(self):
        """Test des permissions"""
        self.assertFalse(self.user.can_manage_users())
        self.assertFalse(self.user.can_manage_menu())
        self.assertTrue(self.user.can_take_orders())
        self.assertFalse(self.user.can_view_reports())
    
    def test_str_representation(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.user), 'Test User (Serveur)')


class UserViewsTest(TestCase):
    """
    Tests des vues
    """
    
    def setUp(self):
        self.client = Client()
        self.admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        self.waiter = CustomUser.objects.create_user(
            username='waiter',
            email='waiter@example.com',
            password='waiter123',
            role='waiter'
        )
    
    def test_login_view_get(self):
        """Test de la page de connexion (GET)"""
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
    
    def test_login_view_post_success(self):
        """Test de connexion réussie (POST)"""
        response = self.client.post(reverse('users:login'), {
            'username': 'waiter',
            'password': 'waiter123'
        })
        self.assertEqual(response.status_code, 302)  # Redirection
    
    def test_login_view_post_failure(self):
        """Test de connexion échouée (POST)"""
        response = self.client.post(reverse('users:login'), {
            'username': 'waiter',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incorrect')
    
    def test_profile_view_requires_login(self):
        """Test que la page profil nécessite une connexion"""
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_profile_view_authenticated(self):
        """Test de la page profil avec utilisateur connecté"""
        self.client.login(username='waiter', password='waiter123')
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
    
    def test_user_list_view_admin_access(self):
        """Test que seul l'admin peut accéder à la liste des utilisateurs"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('users:user_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_user_list_view_waiter_denied(self):
        """Test que le serveur ne peut pas accéder à la liste des utilisateurs"""
        self.client.login(username='waiter', password='waiter123')
        response = self.client.get(reverse('users:user_list'))
        self.assertEqual(response.status_code, 302)  # Redirection