"""
Django TestCase for Restaurant Admin configuration.

This test suite validates the Django admin customizations for the Restaurant model,
ensuring that the admin interface is properly configured with enhanced features.

Run with: python manage.py test home.tests.test_restaurant_admin
"""

from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.urls import reverse

from home.models import Restaurant
from home.admin import RestaurantAdmin


class RestaurantAdminConfigTests(TestCase):
    """Test cases for RestaurantAdmin configuration."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create a superuser for admin access
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create test restaurants
        cls.restaurant1 = Restaurant.objects.create(
            name='Perpex Bistro',
            owner_name='John Doe',
            email='perpex@bistro.com',
            phone_number='555-1234',
            opening_hours={'Monday': '9am-10pm', 'Tuesday': '9am-10pm'}
        )
        
        cls.restaurant2 = Restaurant.objects.create(
            name='La Cuisine',
            owner_name='Jane Smith',
            email='jane@lacuisine.com',
            phone_number='555-5678',
            opening_hours={'Monday': '11am-11pm'}
        )
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.site = AdminSite()
        self.admin = RestaurantAdmin(Restaurant, self.site)
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')
    
    def test_restaurant_admin_class_exists(self):
        """Test that RestaurantAdmin class is properly defined."""
        self.assertIsNotNone(RestaurantAdmin)
        self.assertTrue(hasattr(RestaurantAdmin, 'list_display'))
    
    def test_list_display_configuration(self):
        """Test that list_display includes required fields."""
        expected_fields = ('name', 'owner_name', 'phone_number', 'email', 'created_at')
        self.assertEqual(self.admin.list_display, expected_fields)
    
    def test_list_display_contains_name(self):
        """Test that 'name' is in list_display."""
        self.assertIn('name', self.admin.list_display)
    
    def test_list_display_contains_phone_number(self):
        """Test that 'phone_number' is in list_display."""
        self.assertIn('phone_number', self.admin.list_display)
    
    def test_list_display_contains_email(self):
        """Test that 'email' is in list_display."""
        self.assertIn('email', self.admin.list_display)
    
    def test_search_fields_configuration(self):
        """Test that search_fields is properly configured."""
        self.assertTrue(hasattr(self.admin, 'search_fields'))
        self.assertIsInstance(self.admin.search_fields, (list, tuple))
    
    def test_search_fields_contains_name(self):
        """Test that 'name' is in search_fields."""
        self.assertIn('name', self.admin.search_fields)
    
    def test_search_fields_contains_owner_name(self):
        """Test that 'owner_name' is in search_fields."""
        self.assertIn('owner_name', self.admin.search_fields)
    
    def test_readonly_fields_configuration(self):
        """Test that readonly_fields includes created_at."""
        self.assertTrue(hasattr(self.admin, 'readonly_fields'))
        self.assertIn('created_at', self.admin.readonly_fields)
    
    def test_ordering_configuration(self):
        """Test that ordering is set to name."""
        self.assertTrue(hasattr(self.admin, 'ordering'))
        self.assertEqual(self.admin.ordering, ('name',))
    
    def test_fieldsets_configuration(self):
        """Test that fieldsets are properly organized."""
        self.assertTrue(hasattr(self.admin, 'fieldsets'))
        self.assertIsInstance(self.admin.fieldsets, tuple)
        self.assertEqual(len(self.admin.fieldsets), 4)
    
    def test_admin_registration(self):
        """Test that Restaurant model is registered with RestaurantAdmin."""
        from django.contrib import admin
        
        # Check if Restaurant is registered
        self.assertIn(Restaurant, admin.site._registry)
        
        # Check if it's registered with RestaurantAdmin
        registered_admin = admin.site._registry[Restaurant]
        self.assertIsInstance(registered_admin, RestaurantAdmin)


class RestaurantAdminViewTests(TestCase):
    """Test cases for Restaurant admin interface views."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        cls.admin_user = User.objects.create_superuser(
            username='testadmin',
            email='testadmin@test.com',
            password='testpass123'
        )
        
        # Create test restaurants
        Restaurant.objects.create(
            name='Test Restaurant 1',
            owner_name='Owner One',
            email='owner1@test.com',
            phone_number='555-0001'
        )
        
        Restaurant.objects.create(
            name='Test Restaurant 2',
            owner_name='Owner Two',
            email='owner2@test.com',
            phone_number='555-0002'
        )
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = Client()
        self.client.login(username='testadmin', password='testpass123')
    
    def test_admin_changelist_accessible(self):
        """Test that restaurant list view is accessible in admin."""
        url = reverse('admin:home_restaurant_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_admin_changelist_displays_restaurants(self):
        """Test that restaurants are displayed in the admin list."""
        url = reverse('admin:home_restaurant_changelist')
        response = self.client.get(url)
        
        self.assertContains(response, 'Test Restaurant 1')
        self.assertContains(response, 'Test Restaurant 2')
    
    def test_admin_changelist_displays_contact_info(self):
        """Test that contact information is displayed in the list."""
        url = reverse('admin:home_restaurant_changelist')
        response = self.client.get(url)
        
        self.assertContains(response, '555-0001')
        self.assertContains(response, 'owner1@test.com')
    
    def test_admin_search_by_name(self):
        """Test that search functionality works for restaurant name."""
        url = reverse('admin:home_restaurant_changelist')
        response = self.client.get(url, {'q': 'Test Restaurant 1'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Restaurant 1')
    
    def test_admin_search_by_owner(self):
        """Test that search functionality works for owner name."""
        url = reverse('admin:home_restaurant_changelist')
        response = self.client.get(url, {'q': 'Owner Two'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Restaurant 2')
    
    def test_admin_change_view_accessible(self):
        """Test that individual restaurant edit view is accessible."""
        restaurant = Restaurant.objects.first()
        url = reverse('admin:home_restaurant_change', args=[restaurant.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_admin_add_view_accessible(self):
        """Test that add restaurant view is accessible."""
        url = reverse('admin:home_restaurant_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_admin_requires_authentication(self):
        """Test that admin views require authentication."""
        self.client.logout()
        url = reverse('admin:home_restaurant_changelist')
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


class RestaurantAdminFieldsetsTests(TestCase):
    """Test cases for RestaurantAdmin fieldsets organization."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.site = AdminSite()
        self.admin = RestaurantAdmin(Restaurant, self.site)
    
    def test_fieldsets_has_basic_information(self):
        """Test that Basic Information section exists."""
        fieldset_names = [fs[0] for fs in self.admin.fieldsets]
        self.assertIn('Basic Information', fieldset_names)
    
    def test_fieldsets_has_contact_details(self):
        """Test that Contact Details section exists."""
        fieldset_names = [fs[0] for fs in self.admin.fieldsets]
        self.assertIn('Contact Details', fieldset_names)
    
    def test_fieldsets_has_operating_hours(self):
        """Test that Operating Hours section exists."""
        fieldset_names = [fs[0] for fs in self.admin.fieldsets]
        self.assertIn('Operating Hours', fieldset_names)
    
    def test_fieldsets_has_system_information(self):
        """Test that System Information section exists."""
        fieldset_names = [fs[0] for fs in self.admin.fieldsets]
        self.assertIn('System Information', fieldset_names)
    
    def test_basic_info_contains_name(self):
        """Test that Basic Information contains name field."""
        basic_info = self.admin.fieldsets[0]
        self.assertIn('name', basic_info[1]['fields'])
    
    def test_basic_info_contains_owner_name(self):
        """Test that Basic Information contains owner_name field."""
        basic_info = self.admin.fieldsets[0]
        self.assertIn('owner_name', basic_info[1]['fields'])
    
    def test_contact_details_contains_email(self):
        """Test that Contact Details contains email field."""
        contact_details = self.admin.fieldsets[1]
        self.assertIn('email', contact_details[1]['fields'])
    
    def test_contact_details_contains_phone(self):
        """Test that Contact Details contains phone_number field."""
        contact_details = self.admin.fieldsets[1]
        self.assertIn('phone_number', contact_details[1]['fields'])


if __name__ == '__main__':
    print("=" * 80)
    print("RESTAURANT ADMIN CONFIGURATION TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test home.tests.test_restaurant_admin")
    print("\nThis test suite covers:")
    print("  ✓ RestaurantAdmin class configuration")
    print("  ✓ list_display attributes")
    print("  ✓ search_fields functionality")
    print("  ✓ readonly_fields configuration")
    print("  ✓ Admin registration verification")
    print("  ✓ Admin views accessibility")
    print("  ✓ Search functionality")
    print("  ✓ Fieldsets organization")
    print("=" * 80)
