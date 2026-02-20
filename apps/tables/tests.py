from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from apps.users.models import CustomUser
from .models import Table, TableMerge, Reservation


class TableModelTest(TestCase):
    """
    Tests du modèle Table
    """
    
    def setUp(self):
        self.table = Table.objects.create(
            number=1,
            capacity=4,
            zone='main_hall',
            status='available'
        )
    
    def test_table_creation(self):
        """Test de création de table"""
        self.assertEqual(self.table.number, 1)
        self.assertEqual(self.table.capacity, 4)
        self.assertTrue(self.table.is_available())
    
    def test_table_str(self):
        """Test de la représentation string"""
        self.assertIn('Table 1', str(self.table))
    
    def test_set_occupied(self):
        """Test de marquage comme occupée"""
        self.assertTrue(self.table.set_occupied())
        self.assertEqual(self.table.status, 'occupied')
        self.assertTrue(self.table.is_occupied())
    
    def test_set_available(self):
        """Test de marquage comme libre"""
        self.table.status = 'occupied'
        self.table.save()
        self.table.set_available()
        self.assertEqual(self.table.status, 'available')


class ReservationModelTest(TestCase):
    """
    Tests du modèle Reservation
    """
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='manager',
            password='test123',
            role='manager'
        )
        
        self.table = Table.objects.create(
            number=1,
            capacity=4
        )
        
        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        
        self.reservation = Reservation.objects.create(
            table=self.table,
            customer_name='John Doe',
            customer_phone='0612345678',
            num_guests=4,
            date=tomorrow,
            time=datetime.time(19, 0),
            created_by=self.user
        )
    
    def test_reservation_creation(self):
        """Test de création de réservation"""
        self.assertEqual(self.reservation.customer_name, 'John Doe')
        self.assertEqual(self.reservation.num_guests, 4)
        self.assertEqual(self.reservation.status, 'pending')
    
    def test_confirm_reservation(self):
        """Test de confirmation de réservation"""
        self.assertTrue(self.reservation.confirm(self.user))
        self.assertEqual(self.reservation.status, 'confirmed')
        self.assertEqual(self.table.status, 'reserved')
    
    def test_cancel_reservation(self):
        """Test d'annulation de réservation"""
        self.assertTrue(self.reservation.cancel())
        self.assertEqual(self.reservation.status, 'cancelled')


class TableViewsTest(TestCase):
    """
    Tests des vues
    """
    
    def setUp(self):
        self.client = Client()
        
        self.manager = CustomUser.objects.create_user(
            username='manager',
            password='test123',
            role='manager'
        )
        
        self.waiter = CustomUser.objects.create_user(
            username='waiter',
            password='test123',
            role='waiter'
        )
        
        self.table = Table.objects.create(
            number=1,
            capacity=4
        )
    
    def test_table_list_requires_login(self):
        """Test que la liste des tables nécessite une connexion"""
        response = self.client.get(reverse('tables:table_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_table_list_authenticated(self):
        """Test de la liste des tables avec utilisateur connecté"""
        self.client.login(username='waiter', password='test123')
        response = self.client.get(reverse('tables:table_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_table_create_manager_access(self):
        """Test que le manager peut créer une table"""
        self.client.login(username='manager', password='test123')
        response = self.client.get(reverse('tables:table_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_table_create_waiter_denied(self):
        """Test que le serveur ne peut pas créer de table"""
        self.client.login(username='waiter', password='test123')
        response = self.client.get(reverse('tables:table_create'))
        self.assertEqual(response.status_code, 302)