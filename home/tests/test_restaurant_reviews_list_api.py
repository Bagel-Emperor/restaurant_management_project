"""
Tests for Restaurant Reviews List API endpoint.

This module tests the /api/restaurant-reviews/ endpoint which returns
paginated restaurant reviews with filtering capabilities.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from home.models import Restaurant, MenuItem, MenuCategory, UserReview

User = get_user_model()


class RestaurantReviewsListAPITests(TestCase):
    """Test suite for Restaurant Reviews List API endpoint."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        self.url = reverse('restaurant-reviews')
        
        # Create restaurant
        self.restaurant = Restaurant.objects.create(
            name='Perpex Bistro',
            owner_name='John Doe',
            email='contact@perpexbistro.com',
            phone_number='555-0123'
        )
        
        # Create category
        self.category = MenuCategory.objects.create(
            name='Main Course',
            description='Delicious main courses'
        )
        
        # Create menu items
        self.pizza = MenuItem.objects.create(
            name='Margherita Pizza',
            description='Classic tomato and mozzarella',
            price=12.99,
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.pasta = MenuItem.objects.create(
            name='Carbonara Pasta',
            description='Creamy pasta with bacon',
            price=14.99,
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        # Create users
        self.user1 = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password='password123'
        )
        
        self.user2 = User.objects.create_user(
            username='jane_smith',
            email='jane@example.com',
            password='password123'
        )
        
        # Create reviews
        self.review1 = UserReview.objects.create(
            user=self.user1,
            menu_item=self.pizza,
            rating=5,
            comment='Absolutely delicious! The best pizza I have ever had in my life.'
        )
        
        self.review2 = UserReview.objects.create(
            user=self.user2,
            menu_item=self.pizza,
            rating=4,
            comment='Very good pizza, would recommend to everyone I know.'
        )
        
        self.review3 = UserReview.objects.create(
            user=self.user1,
            menu_item=self.pasta,
            rating=3,
            comment='Decent pasta but could be better with more seasoning.'
        )
    
    def test_get_reviews_list_success(self):
        """Test successful retrieval of reviews list."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have pagination and reviews keys
        self.assertIn('pagination', response.data)
        self.assertIn('reviews', response.data)
    
    def test_reviews_pagination_structure(self):
        """Test pagination metadata structure."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pagination = response.data['pagination']
        
        # Check pagination fields
        expected_fields = {'page_number', 'page_size', 'total_reviews', 'total_pages', 'next', 'previous'}
        actual_fields = set(pagination.keys())
        
        self.assertEqual(expected_fields, actual_fields)
    
    def test_reviews_pagination_values(self):
        """Test pagination metadata values."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pagination = response.data['pagination']
        
        # page_size shows actual items on page (3 reviews), not configured default
        self.assertEqual(pagination['page_number'], 1)
        self.assertEqual(pagination['page_size'], 3)  # Actual items returned
        self.assertEqual(pagination['total_reviews'], 3)
        self.assertEqual(pagination['total_pages'], 1)
        self.assertIsNone(pagination['previous'])
        self.assertIsNone(pagination['next'])
    
    def test_reviews_list_content(self):
        """Test that reviews list contains expected data."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # Should have 3 reviews
        self.assertEqual(len(reviews), 3)
        
        # Check first review structure
        review = reviews[0]
        expected_fields = {
            'id', 'user', 'user_username', 'menu_item', 
            'menu_item_name', 'rating', 'comment', 'review_date'
        }
        actual_fields = set(review.keys())
        
        self.assertEqual(expected_fields, actual_fields)
    
    def test_reviews_ordered_by_most_recent(self):
        """Test that reviews are ordered by most recent first."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # Most recent should be first (review3, then review2, then review1)
        self.assertEqual(reviews[0]['id'], self.review3.id)
        self.assertEqual(reviews[1]['id'], self.review2.id)
        self.assertEqual(reviews[2]['id'], self.review1.id)
    
    def test_review_data_accuracy(self):
        """Test that review data is accurate."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # Find review1
        review1_data = next(r for r in reviews if r['id'] == self.review1.id)
        
        self.assertEqual(review1_data['user'], self.user1.id)
        self.assertEqual(review1_data['user_username'], 'john_doe')
        self.assertEqual(review1_data['menu_item'], self.pizza.id)
        self.assertEqual(review1_data['menu_item_name'], 'Margherita Pizza')
        self.assertEqual(review1_data['rating'], 5)
        self.assertIn('delicious', review1_data['comment'].lower())
    
    def test_filter_by_rating(self):
        """Test filtering reviews by rating."""
        # Filter for 5-star reviews only
        response = self.client.get(self.url, {'rating': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # Should only have review1
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]['rating'], 5)
        self.assertEqual(reviews[0]['id'], self.review1.id)
    
    def test_filter_by_menu_item(self):
        """Test filtering reviews by menu item."""
        # Filter for pizza reviews only
        response = self.client.get(self.url, {'menu_item': self.pizza.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # Should have 2 reviews for pizza
        self.assertEqual(len(reviews), 2)
        for review in reviews:
            self.assertEqual(review['menu_item'], self.pizza.id)
    
    def test_filter_by_user(self):
        """Test filtering reviews by user."""
        # Filter for user1's reviews only
        response = self.client.get(self.url, {'user': self.user1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # user1 has 2 reviews
        self.assertEqual(len(reviews), 2)
        for review in reviews:
            self.assertEqual(review['user'], self.user1.id)
    
    def test_filter_invalid_rating(self):
        """Test filtering with invalid rating (should be ignored)."""
        # Invalid rating (> 5)
        response = self.client.get(self.url, {'rating': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return all reviews (filter ignored)
        reviews = response.data['reviews']
        self.assertEqual(len(reviews), 3)
    
    def test_filter_non_numeric_rating(self):
        """Test filtering with non-numeric rating (should be ignored)."""
        response = self.client.get(self.url, {'rating': 'abc'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return all reviews (filter ignored)
        reviews = response.data['reviews']
        self.assertEqual(len(reviews), 3)
    
    def test_multiple_filters(self):
        """Test combining multiple filters."""
        # Filter for user1's 5-star reviews
        response = self.client.get(self.url, {
            'user': self.user1.id,
            'rating': 5
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # Should have 1 review (user1's pizza review)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]['user'], self.user1.id)
        self.assertEqual(reviews[0]['rating'], 5)
    
    def test_pagination_with_multiple_pages(self):
        """Test pagination when reviews span multiple pages."""
        # Create additional menu items to avoid unique constraint
        additional_items = []
        for i in range(15):
            item = MenuItem.objects.create(
                name=f'Test Item {i}',
                price='10.99',
                restaurant=self.restaurant,
                category=self.category,
                is_available=True
            )
            additional_items.append(item)
        
        # Create 15 more reviews (total 18)
        for i in range(15):
            UserReview.objects.create(
                user=self.user1 if i % 2 else self.user2,
                menu_item=additional_items[i],
                rating=(i % 5) + 1,
                comment=f'Test review number {i} with sufficient length to pass validation.'
            )
        
        # Request page 1 with page_size=10
        response = self.client.get(self.url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pagination = response.data['pagination']
        
        # Should have 10 reviews on page 1
        self.assertEqual(len(response.data['reviews']), 10)
        self.assertEqual(pagination['page_number'], 1)
        self.assertEqual(pagination['total_reviews'], 18)
        self.assertEqual(pagination['total_pages'], 2)
        self.assertIsNotNone(pagination['next'])
        self.assertIsNone(pagination['previous'])
    
    def test_pagination_page_2(self):
        """Test retrieving page 2 of reviews."""
        # Create additional menu items to avoid unique constraint
        additional_items = []
        for i in range(15):
            item = MenuItem.objects.create(
                name=f'Page2 Item {i}',
                price='11.99',
                restaurant=self.restaurant,
                category=self.category,
                is_available=True
            )
            additional_items.append(item)
        
        # Create 15 more reviews
        for i in range(15):
            UserReview.objects.create(
                user=self.user2 if i % 2 else self.user1,
                menu_item=additional_items[i],
                rating=5,
                comment=f'Test review {i} with enough characters to be valid.'
            )
        
        # Request page 2
        response = self.client.get(self.url, {'page': 2, 'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pagination = response.data['pagination']
        
        # Should have 8 reviews on page 2 (18 total - 10 on page 1)
        self.assertEqual(len(response.data['reviews']), 8)
        self.assertEqual(pagination['page_number'], 2)
        self.assertIsNotNone(pagination['previous'])
        self.assertIsNone(pagination['next'])
    
    def test_custom_page_size(self):
        """Test custom page_size parameter."""
        response = self.client.get(self.url, {'page_size': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        pagination = response.data['pagination']
        
        # Should have 2 reviews per page
        self.assertEqual(len(reviews), 2)
        self.assertEqual(pagination['page_size'], 2)
        self.assertEqual(pagination['total_pages'], 2)  # 3 reviews / 2 per page
    
    def test_reviews_public_access(self):
        """Test that reviews endpoint is publicly accessible."""
        # Ensure no authentication
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        
        # Should still be accessible
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reviews', response.data)
    
    def test_empty_reviews_list(self):
        """Test response when no reviews exist."""
        # Delete all reviews
        UserReview.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have empty reviews array
        self.assertEqual(len(response.data['reviews']), 0)
        
        pagination = response.data['pagination']
        self.assertEqual(pagination['total_reviews'], 0)
        # Django paginator returns 1 page even when empty
        self.assertEqual(pagination['total_pages'], 1)
    
    def test_reviews_method_not_allowed(self):
        """Test that only GET method is allowed."""
        # Try POST
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try PUT
        response = self.client.put(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try DELETE
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_reviews_include_usernames(self):
        """Test that reviews include user_username field."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # All reviews should have user_username
        for review in reviews:
            self.assertIn('user_username', review)
            self.assertIsNotNone(review['user_username'])
            self.assertIn(review['user_username'], ['john_doe', 'jane_smith'])
    
    def test_reviews_include_menu_item_names(self):
        """Test that reviews include menu_item_name field."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        
        # All reviews should have menu_item_name
        for review in reviews:
            self.assertIn('menu_item_name', review)
            self.assertIsNotNone(review['menu_item_name'])
            self.assertIn(review['menu_item_name'], ['Margherita Pizza', 'Carbonara Pasta'])
    
    def test_filter_no_results(self):
        """Test filtering that returns no results."""
        # Filter for non-existent rating
        response = self.client.get(self.url, {'rating': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = response.data['reviews']
        self.assertEqual(len(reviews), 0)
        
        pagination = response.data['pagination']
        self.assertEqual(pagination['total_reviews'], 0)
