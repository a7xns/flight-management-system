from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import PassengerProfile
from .forms import PassengerCreationForm, EmailAuthenticationForm


class PassengerRegistrationTests(TestCase):
    """Test cases for passenger registration view and form."""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('passenger_register')
    
    def test_registration_page_loads(self):
        """Test that the passenger registration page loads successfully."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/passenger_register.html')
        self.assertIsInstance(response.context['form'], PassengerCreationForm)
    
    def test_registration_form_exists(self):
        """Test that the registration form is present on the page."""
        response = self.client.get(self.register_url)
        self.assertIn('form', response.context)
    
    def test_successful_passenger_registration(self):
        """Test successful passenger registration with optional fields."""
        data = {
            'email': 'testpassenger@example.com',
            'first_name': 'Test',
            'last_name': 'Passenger',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
            'date_of_birth': '2000-01-01',
            'phone_number': '1234567890',
            'passport': '',
            'nationality': '1234567890'
        }
        response = self.client.post(self.register_url, data)
        
        # Check redirect after successful registration
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_login'))
        
        # Verify user was created with email as username
        self.assertTrue(User.objects.filter(username='testpassenger@example.com').exists())
        
        # Verify passenger profile was created
        user = User.objects.get(username='testpassenger@example.com')
        self.assertTrue(PassengerProfile.objects.filter(user=user).exists())
        profile = PassengerProfile.objects.get(user=user)
        self.assertEqual(profile.phone_number, '1234567890')
    
    def test_registration_password_mismatch(self):
        """Test that registration fails when passwords don't match."""
        data = {
            'username': 'testpassenger',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpass123!',
            'password2': 'differentpass123!',
            'date_of_birth': '2000-01-01',
            'phone_number': '1234567890',
            'passport': 'ABC123456',
            'nationality': '1234567890'
        }
        response = self.client.post(self.register_url, data)
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testpassenger').exists())
    
    # users/tests.py (Inside PassengerRegistrationTests class)

def test_registration_duplicate_username(self):
    """Test that registration fails with duplicate email (since email = username)."""
    # 1. Create a user with a specific email
    User.objects.create_user(
        username='existing@example.com', # Username is usually email in your system
        email='existing@example.com',
        password='password123'
    )
    
    data = {
        'username': 'whatever', 
        'email': 'existing@example.com',
        'first_name': 'New',
        'last_name': 'User',
        'password1': 'complexpass123!',
        'password2': 'complexpass123!',
        'date_of_birth': '2000-01-01',
        'phone_number': '1234567890',
        'passport': 'XYZ123456',
        'nationality': '1234567890'
    }
    response = self.client.post(self.register_url, data)
    
    # Now this should be 200 (Form Error) because the email exists
    self.assertEqual(response.status_code, 200)
    self.assertIn('form', response.context)
    
    def test_registration_invalid_email(self):
        """Test that registration fails with invalid email."""
        data = {
            'username': 'testuser',
            'email': 'invalidemail',  # Missing @ and domain
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
            'date_of_birth': '2000-01-01',
            'phone_number': '1234567890',
            'passport': 'ABC123456',
            'nationality': '1234567890'
        }
        response = self.client.post(self.register_url, data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser').exists())


class UserLoginTests(TestCase):
    """Test cases for user login view and form."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('user_login')
        
        # Create a test passenger user
        self.user = User.objects.create_user(
            username='testpassenger',
            email='testpassenger@example.com',
            password='testpass123'
        )
        PassengerProfile.objects.create(
            user=self.user,
            passport='ABC1234',
            phone_number='1234567890',
            nationality='American'
        )
        
        # Create a test admin user
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='adminpass123',
            is_staff=True
        )
    
    def test_login_page_loads(self):
        """Test that the login page loads successfully."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertIsInstance(response.context['form'], EmailAuthenticationForm)
    
    def test_login_page_contains_form(self):
        """Test that login page contains the authentication form."""
        response = self.client.get(self.login_url)
        self.assertIn('form', response.context)
    
    def test_successful_passenger_login(self):
        """Test successful login for a passenger user."""
        data = {
            'username': 'testpassenger@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        # Check that user is redirected to passenger dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('passenger_dashboard'))
        
        # Check that user is authenticated
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
    
    def test_successful_admin_login(self):
        """Test successful login for an admin user."""
        data = {
            'username': 'testadmin@example.com',
            'password': 'adminpass123'
        }
        response = self.client.post(self.login_url, data)
        
        # Admin should be redirected to admin index
        self.assertEqual(response.status_code, 302)
        self.assertTrue('admin' in response.url)
    
    def test_login_with_invalid_email(self):
        """Test login fails with non-existent email."""
        data = {
            'username': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        # Should not redirect, stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_wrong_password(self):
        """Test login fails with wrong password."""
        data = {
            'username': 'testpassenger@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_empty_fields(self):
        """Test login fails with empty email or password."""
        data = {
            'username': '',
            'password': ''
        }
        response = self.client.post(self.login_url, data)
        
        # Should not redirect
        self.assertEqual(response.status_code, 200)


class PassengerDashboardTests(TestCase):
    """Test cases for passenger dashboard view."""
    
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('passenger_dashboard')
        
        # Create a passenger user
        self.user = User.objects.create_user(
            username='testpassenger',
            email='testpassenger@example.com',
            password='testpass123'
        )
        self.profile = PassengerProfile.objects.create(
            user=self.user,
            passport='ABC1234',
            phone_number='1234567890',
            nationality='American'
        )
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(self.dashboard_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_loads_for_authenticated_user(self):
        """Test that dashboard loads for authenticated passenger."""
        self.client.login(username='testpassenger', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/passenger_dashboard.html')
    
    def test_dashboard_context_contains_airports_and_bookings(self):
        """Test that dashboard context has airports and bookings data."""
        self.client.login(username='testpassenger', password='testpass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertIn('airports', response.context)
        self.assertIn('upcoming_bookings', response.context)


class AdminDashboardTests(TestCase):
    """Test cases for admin dashboard view."""
    
    def setUp(self):
        self.client = Client()
        self.admin_dashboard_url = reverse('admin_dashboard')
        
        # Create a regular passenger user
        self.passenger = User.objects.create_user(
            username='passenger',
            email='passenger@example.com',
            password='pass123'
        )
        
        # Create an admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
    
    def test_admin_dashboard_requires_login(self):
        """Test that admin dashboard requires authentication."""
        response = self.client.get(self.admin_dashboard_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_passenger_cannot_access_admin_dashboard(self):
        """Test that regular passenger cannot access admin dashboard."""
        self.client.login(username='passenger', password='pass123')
        response = self.client.get(self.admin_dashboard_url)
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('passenger_dashboard'))
    
    def test_admin_can_access_admin_dashboard(self):
        """Test that admin user can access admin dashboard."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(self.admin_dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/admin_dashboard.html')
    
    def test_admin_dashboard_context(self):
        """Test that admin dashboard renders without error."""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(self.admin_dashboard_url)
        
        self.assertEqual(response.status_code, 200)


class ViewProfileTests(TestCase):
    """Test cases for view profile view."""
    
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('profile')
        
        # Create a passenger user
        self.user = User.objects.create_user(
            username='testpassenger',
            email='testpassenger@example.com',
            password='testpass123'
        )
        self.profile = PassengerProfile.objects.create(
            user=self.user,
            passport='ABC1234',
            phone_number='1234567890',
            nationality='American'
        )
    
    def test_profile_requires_login(self):
        """Test that profile view requires authentication."""
        response = self.client.get(self.profile_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_profile_view_loads_for_authenticated_user(self):
        """Test that profile page loads for authenticated user."""
        self.client.login(username='testpassenger', password='testpass123')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
    
    def test_profile_context_contains_passenger_data(self):
        """Test that profile context contains user and profile data."""
        self.client.login(username='testpassenger', password='testpass123')
        response = self.client.get(self.profile_url)
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile'], self.profile)


class UserLogoutTests(TestCase):
    """Test cases for user logout functionality."""
    
    def setUp(self):
        self.client = Client()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        PassengerProfile.objects.create(
            user=self.user,
            passport='ABC1234',
            phone_number='1234567890',
            nationality='American'
        )
    
    def test_logout_requires_login(self):
        """Test that logout endpoint requires authentication."""
        response = self.client.get(reverse('user_logout'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_successful_logout(self):
        """Test that user is logged out successfully."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Verify user is authenticated
        response = self.client.get(reverse('passenger_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Logout
        response = self.client.get(reverse('user_logout'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_login'))
        
        # Verify user is no longer authenticated
        response = self.client.get(reverse('passenger_dashboard'))
        self.assertEqual(response.status_code, 302)
