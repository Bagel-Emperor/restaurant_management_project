"""
Django TestCase for Restaurant has_delivery field.

This test suite validates the has_delivery field functionality including:
1. Field exists and has correct default value
2. Field can be set to True/False
3. Field is properly saved and retrieved from database
4. Field validation and behavior

Run with: python manage.py test home.tests.test_has_delivery_field
"""

from django.test import TestCase
from home.models import Restaurant


class RestaurantHasDeliveryFieldTests(TestCase):
    """Test cases for the Restaurant has_delivery field."""
    
    def test_has_delivery_field_exists(self):
        """Test that has_delivery field exists on Restaurant model."""
        restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='555-0000'
        )
        
        # Verify field exists
        self.assertTrue(hasattr(restaurant, 'has_delivery'))
    
    def test_has_delivery_default_is_false(self):
        """Test that has_delivery defaults to False."""
        restaurant = Restaurant.objects.create(
            name='Default Restaurant',
            owner_name='Default Owner',
            email='default@restaurant.com',
            phone_number='555-0001'
        )
        
        self.assertFalse(restaurant.has_delivery)
    
    def test_has_delivery_can_be_set_to_true(self):
        """Test that has_delivery can be explicitly set to True."""
        restaurant = Restaurant.objects.create(
            name='Delivery Restaurant',
            owner_name='Delivery Owner',
            email='delivery@restaurant.com',
            phone_number='555-0002',
            has_delivery=True
        )
        
        self.assertTrue(restaurant.has_delivery)
    
    def test_has_delivery_can_be_set_to_false(self):
        """Test that has_delivery can be explicitly set to False."""
        restaurant = Restaurant.objects.create(
            name='No Delivery Restaurant',
            owner_name='No Delivery Owner',
            email='nodelivery@restaurant.com',
            phone_number='555-0003',
            has_delivery=False
        )
        
        self.assertFalse(restaurant.has_delivery)
    
    def test_has_delivery_persists_in_database(self):
        """Test that has_delivery value persists after save."""
        restaurant = Restaurant.objects.create(
            name='Persist Restaurant',
            owner_name='Persist Owner',
            email='persist@restaurant.com',
            phone_number='555-0004',
            has_delivery=True
        )
        
        # Retrieve from database
        retrieved = Restaurant.objects.get(pk=restaurant.pk)
        self.assertTrue(retrieved.has_delivery)
    
    def test_has_delivery_can_be_updated(self):
        """Test that has_delivery can be updated after creation."""
        restaurant = Restaurant.objects.create(
            name='Update Restaurant',
            owner_name='Update Owner',
            email='update@restaurant.com',
            phone_number='555-0005',
            has_delivery=False
        )
        
        # Verify initial value
        self.assertFalse(restaurant.has_delivery)
        
        # Update the field
        restaurant.has_delivery = True
        restaurant.save()
        
        # Verify update persisted
        retrieved = Restaurant.objects.get(pk=restaurant.pk)
        self.assertTrue(retrieved.has_delivery)
    
    def test_has_delivery_is_boolean_type(self):
        """Test that has_delivery is a boolean field."""
        restaurant = Restaurant.objects.create(
            name='Boolean Restaurant',
            owner_name='Boolean Owner',
            email='boolean@restaurant.com',
            phone_number='555-0006',
            has_delivery=True
        )
        
        self.assertIsInstance(restaurant.has_delivery, bool)
    
    def test_multiple_restaurants_different_delivery_status(self):
        """Test that multiple restaurants can have different delivery statuses."""
        restaurant1 = Restaurant.objects.create(
            name='Restaurant With Delivery',
            owner_name='Owner 1',
            email='with@delivery.com',
            phone_number='555-0007',
            has_delivery=True
        )
        
        restaurant2 = Restaurant.objects.create(
            name='Restaurant Without Delivery',
            owner_name='Owner 2',
            email='without@delivery.com',
            phone_number='555-0008',
            has_delivery=False
        )
        
        self.assertTrue(restaurant1.has_delivery)
        self.assertFalse(restaurant2.has_delivery)
    
    def test_filter_restaurants_by_has_delivery(self):
        """Test that restaurants can be filtered by has_delivery status."""
        # Create restaurants with delivery
        Restaurant.objects.create(
            name='Delivery A',
            owner_name='Owner A',
            email='deliverya@test.com',
            phone_number='555-1000',
            has_delivery=True
        )
        Restaurant.objects.create(
            name='Delivery B',
            owner_name='Owner B',
            email='deliveryb@test.com',
            phone_number='555-1001',
            has_delivery=True
        )
        
        # Create restaurants without delivery
        Restaurant.objects.create(
            name='No Delivery A',
            owner_name='Owner C',
            email='nodeliverya@test.com',
            phone_number='555-1002',
            has_delivery=False
        )
        
        # Filter by has_delivery=True
        delivery_restaurants = Restaurant.objects.filter(has_delivery=True)
        self.assertEqual(delivery_restaurants.count(), 2)
        
        # Filter by has_delivery=False
        no_delivery_restaurants = Restaurant.objects.filter(has_delivery=False)
        self.assertEqual(no_delivery_restaurants.count(), 1)
    
    def test_has_delivery_field_in_model_meta(self):
        """Test that has_delivery field is properly defined in model."""
        field = Restaurant._meta.get_field('has_delivery')
        
        # Verify field type
        self.assertEqual(field.get_internal_type(), 'BooleanField')
        
        # Verify default value
        self.assertFalse(field.default)


class RestaurantHasDeliveryQueryTests(TestCase):
    """Test cases for querying restaurants by has_delivery field."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create 3 restaurants with delivery
        for i in range(3):
            Restaurant.objects.create(
                name=f'Delivery Restaurant {i}',
                owner_name=f'Owner {i}',
                email=f'delivery{i}@test.com',
                phone_number=f'555-200{i}',
                has_delivery=True
            )
        
        # Create 2 restaurants without delivery
        for i in range(2):
            Restaurant.objects.create(
                name=f'No Delivery Restaurant {i}',
                owner_name=f'Owner {i+10}',
                email=f'nodelivery{i}@test.com',
                phone_number=f'555-300{i}',
                has_delivery=False
            )
    
    def test_count_restaurants_with_delivery(self):
        """Test counting restaurants that offer delivery."""
        count = Restaurant.objects.filter(has_delivery=True).count()
        self.assertEqual(count, 3)
    
    def test_count_restaurants_without_delivery(self):
        """Test counting restaurants that don't offer delivery."""
        count = Restaurant.objects.filter(has_delivery=False).count()
        self.assertEqual(count, 2)
    
    def test_get_all_delivery_restaurants(self):
        """Test retrieving all restaurants with delivery."""
        delivery_restaurants = Restaurant.objects.filter(has_delivery=True)
        
        for restaurant in delivery_restaurants:
            self.assertTrue(restaurant.has_delivery)
    
    def test_exclude_delivery_restaurants(self):
        """Test excluding restaurants with delivery."""
        no_delivery = Restaurant.objects.exclude(has_delivery=True)
        
        self.assertEqual(no_delivery.count(), 2)
        for restaurant in no_delivery:
            self.assertFalse(restaurant.has_delivery)


if __name__ == '__main__':
    print("=" * 80)
    print("RESTAURANT HAS_DELIVERY FIELD TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test home.tests.test_has_delivery_field")
    print("\nThis test suite covers:")
    print("  ✓ Field existence and default value")
    print("  ✓ Setting and updating has_delivery")
    print("  ✓ Database persistence")
    print("  ✓ Field type validation")
    print("  ✓ Filtering and querying by has_delivery")
    print("  ✓ Multiple restaurants with different statuses")
    print("=" * 80)
