"""
Test suite for Menu Category CRUD API operations.
Tests the full CRUD functionality of MenuCategoryViewSet.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from home.models import MenuCategory


class MenuCategoryCRUDTestCase(TestCase):
    """Test cases for Menu Category CRUD operations."""
    
    def setUp(self):
        """Set up test client and create test data."""
        self.client = APIClient()
        self.list_url = reverse('menucategory-list')
        
        # Create a test user for authenticated operations
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Clear any existing categories to ensure clean test environment
        MenuCategory.objects.all().delete()
        
        # Create test categories
        self.category1 = MenuCategory.objects.create(name="Appetizers")
        self.category2 = MenuCategory.objects.create(name="Main Courses")
        self.category3 = MenuCategory.objects.create(name="Desserts")
    
    def test_list_categories(self):
        """Test listing all menu categories (ordered by name) - public access."""
        # No authentication required for listing
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Response might be paginated (dict with 'results') or a list
        if isinstance(response.data, dict) and 'results' in response.data:
            # Paginated response
            categories = response.data['results']
            self.assertEqual(response.data['count'], 3)
        else:
            # Direct list response
            categories = response.data
        
        # At least 3 categories should exist (from setUp)
        self.assertEqual(len(categories), 3)
        
        # Find our test categories in the response
        category_names = [cat['name'] for cat in categories]
        self.assertIn("Appetizers", category_names)
        self.assertIn("Desserts", category_names)
        self.assertIn("Main Courses", category_names)
        
        # Check ordering (alphabetical by name)
        # Verify that categories are in alphabetical order
        sorted_names = sorted(category_names)
        self.assertEqual(category_names, sorted_names)
    
    def test_retrieve_category(self):
        """Test retrieving a single menu category - public access."""
        # No authentication required for retrieval
        detail_url = reverse('menucategory-detail', kwargs={'pk': self.category1.pk})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.category1.id)
        self.assertEqual(response.data['name'], "Appetizers")
    
    def test_create_category(self):
        """Test creating a new menu category - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        data = {'name': 'Beverages'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Beverages')
        
        # Verify it was created in the database
        self.assertTrue(MenuCategory.objects.filter(name='Beverages').exists())
        self.assertEqual(MenuCategory.objects.count(), 4)
    
    def test_create_duplicate_category(self):
        """Test that duplicate category names are rejected - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        data = {'name': 'Appetizers'}  # Already exists
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should still have only 3 categories
        self.assertEqual(MenuCategory.objects.count(), 3)
    
    def test_update_category_put(self):
        """Test updating a category with PUT (full update) - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        detail_url = reverse('menucategory-detail', kwargs={'pk': self.category1.pk})
        data = {'name': 'Starters'}
        response = self.client.put(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Starters')
        
        # Verify database update
        self.category1.refresh_from_db()
        self.assertEqual(self.category1.name, 'Starters')
    
    def test_update_category_patch(self):
        """Test updating a category with PATCH (partial update) - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        detail_url = reverse('menucategory-detail', kwargs={'pk': self.category2.pk})
        data = {'name': 'Entrees'}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Entrees')
        
        # Verify database update
        self.category2.refresh_from_db()
        self.assertEqual(self.category2.name, 'Entrees')
    
    def test_delete_category(self):
        """Test deleting a menu category - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        detail_url = reverse('menucategory-detail', kwargs={'pk': self.category3.pk})
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify it was deleted from database
        self.assertFalse(MenuCategory.objects.filter(pk=self.category3.pk).exists())
        self.assertEqual(MenuCategory.objects.count(), 2)
    
    def test_retrieve_nonexistent_category(self):
        """Test retrieving a category that doesn't exist - public access."""
        # No authentication required
        detail_url = reverse('menucategory-detail', kwargs={'pk': 9999})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_nonexistent_category(self):
        """Test updating a category that doesn't exist - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        detail_url = reverse('menucategory-detail', kwargs={'pk': 9999})
        data = {'name': 'Nonexistent'}
        response = self.client.put(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_nonexistent_category(self):
        """Test deleting a category that doesn't exist - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        detail_url = reverse('menucategory-detail', kwargs={'pk': 9999})
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_category_empty_name(self):
        """Test that empty category name is rejected - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        data = {'name': ''}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_category_no_name(self):
        """Test that missing category name is rejected - requires authentication."""
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        data = {}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_category_without_auth(self):
        """Test that creating a category without authentication is rejected."""
        # No authentication
        data = {'name': 'Unauthorized Category'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_category_without_auth(self):
        """Test that updating a category without authentication is rejected."""
        # No authentication
        detail_url = reverse('menucategory-detail', kwargs={'pk': self.category1.pk})
        data = {'name': 'Unauthorized Update'}
        response = self.client.put(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_category_without_auth(self):
        """Test that deleting a category without authentication is rejected."""
        # No authentication
        detail_url = reverse('menucategory-detail', kwargs={'pk': self.category1.pk})
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_category_with_description(self):
        """Test creating a category with optional description field."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'name': 'Beverages',
            'description': 'Refreshing drinks including sodas, juices, and specialty beverages'
        }
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Beverages')
        self.assertEqual(response.data['description'], 'Refreshing drinks including sodas, juices, and specialty beverages')
        
        # Verify in database
        category = MenuCategory.objects.get(name='Beverages')
        self.assertEqual(category.description, 'Refreshing drinks including sodas, juices, and specialty beverages')
    
    def test_create_category_without_description(self):
        """Test creating a category without description (optional field)."""
        self.client.force_authenticate(user=self.user)
        
        data = {'name': 'Sides'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Sides')
        self.assertEqual(response.data['description'], '')  # Should be empty string
        
        # Verify in database
        category = MenuCategory.objects.get(name='Sides')
        self.assertEqual(category.description, '')
    
    def test_update_category_description(self):
        """Test updating a category's description."""
        self.client.force_authenticate(user=self.user)
        
        detail_url = reverse('menucategory-detail', kwargs={'pk': self.category1.pk})
        data = {
            'name': 'Appetizers',
            'description': 'Delicious starters to begin your meal'
        }
        response = self.client.put(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Delicious starters to begin your meal')
        
        # Verify in database
        self.category1.refresh_from_db()
        self.assertEqual(self.category1.description, 'Delicious starters to begin your meal')

