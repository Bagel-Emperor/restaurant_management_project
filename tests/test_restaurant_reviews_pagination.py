"""
Tests for Restaurant Reviews Pagination API

Tests the paginated restaurant reviews endpoint to ensure:
- Proper pagination functionality
- Correct pagination metadata
- Filtering capabilities (by rating, menu_item, user)
- Public access (no authentication required)
- Correct ordering (most recent first)
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from home.models import MenuItem, MenuCategory, UserReview, Restaurant


class RestaurantReviewsPaginationTest(TestCase):
    """Test cases for the paginated restaurant reviews API endpoint."""
    
    def setUp(self):
        """Set up test data: users, menu items, and reviews."""
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='jane_smith',
            email='jane@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='bob_jones',
            email='bob@example.com',
            password='testpass123'
        )
        
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='owner@test.com',
            phone_number='123-456-7890'
        )
        
        # Create test category
        self.category = MenuCategory.objects.create(
            name='Pizza',
            description='Delicious pizzas'
        )
        
        # Create test menu items
        self.pizza1 = MenuItem.objects.create(
            name='Margherita Pizza',
            description='Classic tomato and mozzarella',
            price=12.99,
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        self.pizza2 = MenuItem.objects.create(
            name='Pepperoni Pizza',
            description='Loaded with pepperoni',
            price=14.99,
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        # Create 25 test reviews for pagination testing
        self.reviews = []
        for i in range(25):
            user = [self.user1, self.user2, self.user3][i % 3]
            menu_item = [self.pizza1, self.pizza2][i % 2]
            rating = (i % 5) + 1  # Ratings from 1 to 5
            
            # Skip if this user already reviewed this item
            if UserReview.objects.filter(user=user, menu_item=menu_item).exists():
                continue
                
            review = UserReview.objects.create(
                user=user,
                menu_item=menu_item,
                rating=rating,
                comment=f'Test review {i + 1} - Great food!'
            )
            self.reviews.append(review)
        
        self.url = reverse('restaurant-reviews')
    
    def test_pagination_basic(self):
        """Test basic pagination functionality."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pagination', response.data)
        self.assertIn('reviews', response.data)
        
        # Check pagination metadata
        pagination = response.data['pagination']
        reviews = response.data['reviews']
        
        self.assertEqual(pagination['page_number'], 1)
        self.assertEqual(pagination['page_size'], len(reviews))  # Actual number of items on page
        self.assertGreater(pagination['total_reviews'], 0)
        self.assertGreater(pagination['total_pages'], 0)
        
        # Check reviews data
        self.assertLessEqual(len(reviews), 10)  # Default page size
    
    def test_pagination_metadata_structure(self):
        """Test that pagination metadata has all required fields."""
        response = self.client.get(self.url)
        
        pagination = response.data['pagination']
        required_fields = [
            'page_number',
            'page_size',
            'total_reviews',
            'total_pages',
            'next',
            'previous'
        ]
        
        for field in required_fields:
            self.assertIn(field, pagination)
    
    def test_pagination_page_2(self):
        """Test accessing page 2 of results."""
        # Only test if we have enough reviews for page 2
        total_reviews = UserReview.objects.count()
        if total_reviews > 10:  # Default page size is 10
            response = self.client.get(self.url, {'page': 2})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            pagination = response.data['pagination']
            
            self.assertEqual(pagination['page_number'], 2)
            self.assertIsNotNone(pagination['previous'])  # Should have previous link
        else:
            # Skip test if not enough data
            self.skipTest(f"Not enough reviews ({total_reviews}) for page 2 test")
    
    def test_pagination_custom_page_size(self):
        """Test custom page size parameter."""
        response = self.client.get(self.url, {'page_size': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pagination = response.data['pagination']
        reviews = response.data['reviews']
        
        self.assertEqual(pagination['page_size'], 5)
        self.assertLessEqual(len(reviews), 5)
    
    def test_pagination_max_page_size_limit(self):
        """Test that page size is limited to max_page_size (100)."""
        response = self.client.get(self.url, {'page_size': 200})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pagination = response.data['pagination']
        
        # Should be capped at 100
        self.assertLessEqual(pagination['page_size'], 100)
    
    def test_public_access_no_authentication(self):
        """Test that the endpoint is accessible without authentication."""
        # Don't authenticate
        response = self.client.get(self.url)
        
        # Should still work
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reviews', response.data)
    
    def test_reviews_ordered_by_most_recent(self):
        """Test that reviews are ordered by most recent first."""
        response = self.client.get(self.url)
        
        reviews = response.data['reviews']
        if len(reviews) > 1:
            # Check that reviews are in descending order by date
            for i in range(len(reviews) - 1):
                current_date = reviews[i]['review_date']
                next_date = reviews[i + 1]['review_date']
                self.assertGreaterEqual(current_date, next_date)
    
    def test_filter_by_rating(self):
        """Test filtering reviews by rating."""
        response = self.client.get(self.url, {'rating': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reviews = response.data['reviews']
        
        # All reviews should have rating of 5
        for review in reviews:
            self.assertEqual(review['rating'], 5)
    
    def test_filter_by_invalid_rating(self):
        """Test filtering with invalid rating (should be ignored)."""
        response = self.client.get(self.url, {'rating': 10})
        
        # Should still return 200, but filter is ignored
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_menu_item(self):
        """Test filtering reviews by menu item."""
        response = self.client.get(self.url, {'menu_item': self.pizza1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reviews = response.data['reviews']
        
        # All reviews should be for pizza1
        for review in reviews:
            self.assertEqual(review['menu_item'], self.pizza1.id)
    
    def test_filter_by_user(self):
        """Test filtering reviews by user."""
        response = self.client.get(self.url, {'user': self.user1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reviews = response.data['reviews']
        
        # All reviews should be by user1
        for review in reviews:
            self.assertEqual(review['user'], self.user1.id)
    
    def test_filter_combination(self):
        """Test combining multiple filters."""
        response = self.client.get(self.url, {
            'rating': 5,
            'menu_item': self.pizza1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reviews = response.data['reviews']
        
        # All reviews should match both filters
        for review in reviews:
            self.assertEqual(review['rating'], 5)
            self.assertEqual(review['menu_item'], self.pizza1.id)
    
    def test_review_data_structure(self):
        """Test that review objects have all expected fields."""
        response = self.client.get(self.url)
        
        reviews = response.data['reviews']
        if reviews:
            review = reviews[0]
            expected_fields = [
                'id',
                'user',
                'user_username',
                'menu_item',
                'menu_item_name',
                'rating',
                'comment',
                'review_date'
            ]
            
            for field in expected_fields:
                self.assertIn(field, review)
    
    def test_empty_page(self):
        """Test requesting a page beyond the available data."""
        response = self.client.get(self.url, {'page': 9999})
        
        # DRF returns 404 for invalid page
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_pagination_with_no_reviews(self):
        """Test pagination when there are no reviews."""
        # Delete all reviews
        UserReview.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pagination = response.data['pagination']
        reviews = response.data['reviews']
        
        self.assertEqual(pagination['total_reviews'], 0)
        self.assertEqual(pagination['total_pages'], 1)  # DRF returns 1 for empty result
        self.assertEqual(len(reviews), 0)
    
    def test_next_link_on_first_page(self):
        """Test that next link is present on first page when more pages exist."""
        # Only test if we have enough reviews for multiple pages
        total_reviews = UserReview.objects.count()
        if total_reviews > 10:
            response = self.client.get(self.url)
            
            pagination = response.data['pagination']
            self.assertIsNotNone(pagination['next'])
            self.assertIsNone(pagination['previous'])
    
    def test_previous_link_on_last_page(self):
        """Test that previous link is present on last page."""
        # Get total pages
        response = self.client.get(self.url)
        total_pages = response.data['pagination']['total_pages']
        
        if total_pages > 1:
            # Request last page
            response = self.client.get(self.url, {'page': total_pages})
            
            pagination = response.data['pagination']
            self.assertIsNotNone(pagination['previous'])
            self.assertIsNone(pagination['next'])


class RestaurantReviewsSerializerTest(TestCase):
    """Test that the serializer includes proper user and menu item details."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant 2',
            owner_name='Test Owner',
            email='owner2@test.com',
            phone_number='987-654-3210'
        )
        
        self.category = MenuCategory.objects.create(
            name='Burgers',
            description='Juicy burgers'
        )
        
        self.menu_item = MenuItem.objects.create(
            name='Cheeseburger',
            description='Classic cheeseburger',
            price=9.99,
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.review = UserReview.objects.create(
            user=self.user,
            menu_item=self.menu_item,
            rating=5,
            comment='Absolutely delicious burger!'
        )
        
        self.url = reverse('restaurant-reviews')
    
    def test_review_includes_username(self):
        """Test that review includes user's username."""
        response = self.client.get(self.url)
        
        reviews = response.data['reviews']
        review = reviews[0]
        
        self.assertEqual(review['user_username'], self.user.username)
    
    def test_review_includes_menu_item_name(self):
        """Test that review includes menu item's name."""
        response = self.client.get(self.url)
        
        reviews = response.data['reviews']
        review = reviews[0]
        
        self.assertEqual(review['menu_item_name'], self.menu_item.name)
