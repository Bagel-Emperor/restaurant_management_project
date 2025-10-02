"""
Test cases for Table API endpoints.

This module contains comprehensive test cases for the Table management API,
including list and detail endpoints with various filtering scenarios.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from home.models import Restaurant, Table
from django.contrib.auth.models import User


class TableAPITestCase(TestCase):
    """Test case for Table API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='555-0123'
        )
        
        # Create test tables
        self.table1 = Table.objects.create(
            number=1,
            capacity=2,
            location='indoor',
            status='available',
            restaurant=self.restaurant,
            description='Small table by window'
        )
        
        self.table2 = Table.objects.create(
            number=2,
            capacity=4,
            location='outdoor',
            status='occupied',
            restaurant=self.restaurant,
            description='Patio table with umbrella'
        )
        
        self.table3 = Table.objects.create(
            number=3,
            capacity=6,
            location='indoor',
            status='reserved',
            restaurant=self.restaurant,
            is_active=False  # Inactive table
        )
    
    def test_table_list_api(self):
        """Test the table list API endpoint."""
        url = reverse('table-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 3)
        
        # Check first table data
        first_table = response.data['results'][0]
        self.assertEqual(first_table['number'], 1)
        self.assertEqual(first_table['capacity'], 2)
        self.assertEqual(first_table['location'], 'indoor')
        self.assertEqual(first_table['status'], 'available')
        self.assertTrue(first_table['is_available'])
        self.assertEqual(first_table['restaurant_name'], 'Test Restaurant')
    
    def test_table_detail_api(self):
        """Test the table detail API endpoint."""
        url = reverse('table-detail', kwargs={'pk': self.table1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number'], 1)
        self.assertEqual(response.data['capacity'], 2)
        self.assertEqual(response.data['location'], 'indoor')
        self.assertEqual(response.data['location_display'], 'Indoor')
        self.assertEqual(response.data['status'], 'available')
        self.assertEqual(response.data['status_display'], 'Available')
        self.assertTrue(response.data['is_available'])
        self.assertEqual(response.data['description'], 'Small table by window')
    
    def test_table_detail_not_found(self):
        """Test table detail API with non-existent table."""
        url = reverse('table-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_table_list_filter_by_status(self):
        """Test filtering tables by status."""
        url = reverse('table-list')
        response = self.client.get(url, {'status': 'available'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'available')
    
    def test_table_list_filter_by_capacity(self):
        """Test filtering tables by minimum capacity."""
        url = reverse('table-list')
        response = self.client.get(url, {'capacity': '4'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return tables with capacity >= 4 (table2 and table3)
        self.assertEqual(len(response.data['results']), 2)
        capacities = [table['capacity'] for table in response.data['results']]
        self.assertTrue(all(cap >= 4 for cap in capacities))
    
    def test_table_list_filter_by_location(self):
        """Test filtering tables by location."""
        url = reverse('table-list')
        response = self.client.get(url, {'location': 'indoor'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        locations = [table['location'] for table in response.data['results']]
        self.assertTrue(all(loc == 'indoor' for loc in locations))
    
    def test_table_list_filter_active_only(self):
        """Test filtering tables to show only active ones."""
        url = reverse('table-list')
        response = self.client.get(url, {'active_only': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only active tables (table1 and table2)
        self.assertEqual(len(response.data['results']), 2)
        active_statuses = [table['is_active'] for table in response.data['results']]
        self.assertTrue(all(active_statuses))
    
    def test_table_list_filter_by_restaurant(self):
        """Test filtering tables by restaurant ID."""
        # Create another restaurant and table
        other_restaurant = Restaurant.objects.create(
            name='Other Restaurant',
            owner_name='Other Owner',
            email='other@restaurant.com',
            phone_number='555-9876'
        )
        
        Table.objects.create(
            number=10,
            capacity=8,
            location='private',
            status='available',
            restaurant=other_restaurant
        )
        
        url = reverse('table-list')
        response = self.client.get(url, {'restaurant': str(self.restaurant.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only tables for our test restaurant
        self.assertEqual(len(response.data['results']), 3)
        restaurant_ids = [table['restaurant'] for table in response.data['results']]
        self.assertTrue(all(rid == self.restaurant.id for rid in restaurant_ids))
    
    def test_table_list_multiple_filters(self):
        """Test combining multiple filters."""
        url = reverse('table-list')
        response = self.client.get(url, {
            'location': 'indoor',
            'capacity': '2',
            'active_only': 'true'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return table1 only (indoor, capacity>=2, active)
        self.assertEqual(len(response.data['results']), 1)
        table = response.data['results'][0]
        self.assertEqual(table['number'], 1)
        self.assertEqual(table['location'], 'indoor')
        self.assertTrue(table['is_active'])
        self.assertGreaterEqual(table['capacity'], 2)
    
    def test_table_serializer_fields(self):
        """Test that all expected fields are included in serializer."""
        url = reverse('table-detail', kwargs={'pk': self.table1.pk})
        response = self.client.get(url)
        
        expected_fields = {
            'id', 'number', 'capacity', 'location', 'location_display',
            'status', 'status_display', 'is_active', 'is_available',
            'description', 'restaurant', 'restaurant_name',
            'created_at', 'updated_at'
        }
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), expected_fields)
    
    def test_table_number_unique_per_restaurant(self):
        """Test that table numbers are unique per restaurant, not globally."""
        # Create a second restaurant
        restaurant2 = Restaurant.objects.create(
            name='Second Restaurant',
            owner_name='Owner 2',
            email='owner2@test.com',
            phone_number='555-9876'
        )
        
        # Create table 1 in first restaurant (already exists from setUp)
        self.assertEqual(self.table1.number, 1)
        self.assertEqual(self.table1.restaurant, self.restaurant)
        
        # Create table 1 in second restaurant - should be allowed
        table1_restaurant2 = Table.objects.create(
            number=1,
            capacity=4,
            location='outdoor',
            restaurant=restaurant2
        )
        
        self.assertEqual(table1_restaurant2.number, 1)
        self.assertEqual(table1_restaurant2.restaurant, restaurant2)
        
        # Verify both tables exist and have same number but different restaurants
        tables_with_number_1 = Table.objects.filter(number=1)
        self.assertEqual(tables_with_number_1.count(), 2)
        
        # Try to create duplicate table number in same restaurant - should fail
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Table.objects.create(
                number=1,
                capacity=6,
                location='indoor',
                restaurant=self.restaurant  # Same restaurant as table1
            )


class TableModelTestCase(TestCase):
    """Test case for Table model methods and properties."""
    
    def setUp(self):
        """Set up test data."""
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='555-0123'
        )
    
    def test_table_string_representation(self):
        """Test table __str__ method."""
        table = Table.objects.create(
            number=5,
            capacity=4,
            location='indoor',
            status='available',
            restaurant=self.restaurant
        )
        
        expected_str = "Table 5 (4 seats) - Available"
        self.assertEqual(str(table), expected_str)
    
    def test_table_is_available_property(self):
        """Test the is_available property."""
        # Available and active table
        available_table = Table.objects.create(
            number=1,
            capacity=2,
            status='available',
            is_active=True,
            restaurant=self.restaurant
        )
        self.assertTrue(available_table.is_available)
        
        # Occupied table
        occupied_table = Table.objects.create(
            number=2,
            capacity=2,
            status='occupied',
            is_active=True,
            restaurant=self.restaurant
        )
        self.assertFalse(occupied_table.is_available)
        
        # Inactive table
        inactive_table = Table.objects.create(
            number=3,
            capacity=2,
            status='available',
            is_active=False,
            restaurant=self.restaurant
        )
        self.assertFalse(inactive_table.is_available)
    
    def test_table_status_display_property(self):
        """Test the status_display property."""
        table = Table.objects.create(
            number=1,
            capacity=2,
            status='available',
            restaurant=self.restaurant
        )
        
        self.assertEqual(table.status_display, 'Available')
    
    def test_table_clean_validation(self):
        """Test table model validation."""
        from django.core.exceptions import ValidationError
        
        # Test invalid capacity
        table = Table(
            number=1,
            capacity=0,
            restaurant=self.restaurant
        )
        with self.assertRaises(ValidationError):
            table.clean()
        
        # Test invalid table number
        table = Table(
            number=0,
            capacity=2,
            restaurant=self.restaurant
        )
        with self.assertRaises(ValidationError):
            table.clean()