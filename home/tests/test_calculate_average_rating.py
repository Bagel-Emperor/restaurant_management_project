"""
Tests for the calculate_average_rating utility function.

This module tests the calculate_average_rating function from home.utils,
which computes the average rating from a queryset of UserReview objects.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from home.models import Restaurant, MenuItem, MenuCategory, UserReview
from home.utils import calculate_average_rating


class CalculateAverageRatingTests(TestCase):
    """Test cases for the calculate_average_rating utility function."""
    
    def setUp(self):
        """Set up test data for average rating calculations."""
        # Create restaurant
        self.restaurant = Restaurant.objects.create(
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='555-0100'
        )
        
        # Create category
        self.category = MenuCategory.objects.create(
            name='Test Category',
            description='Test category for rating tests'
        )
        
        # Create menu items
        self.item1 = MenuItem.objects.create(
            name='Pizza',
            price='12.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.item2 = MenuItem.objects.create(
            name='Pasta',
            price='14.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        # Create users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='user1@test.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='user2@test.com',
            password='testpass123'
        )
        
        self.user3 = User.objects.create_user(
            username='testuser3',
            email='user3@test.com',
            password='testpass123'
        )
    
    def test_empty_queryset(self):
        """Test that empty queryset returns 0.0."""
        empty_reviews = UserReview.objects.none()
        average = calculate_average_rating(empty_reviews)
        
        self.assertEqual(average, 0.0)
        self.assertIsInstance(average, float)
    
    def test_no_reviews_exists(self):
        """Test that when no reviews exist, it returns 0.0."""
        all_reviews = UserReview.objects.all()
        average = calculate_average_rating(all_reviews)
        
        self.assertEqual(average, 0.0)
    
    def test_single_review(self):
        """Test average rating with a single review."""
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=5,
            comment='Excellent pizza with great taste and quality!'
        )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 5.0)
    
    def test_multiple_reviews_same_rating(self):
        """Test average when all reviews have the same rating."""
        for i in range(3):
            UserReview.objects.create(
                user=self.user1 if i == 0 else (self.user2 if i == 1 else self.user3),
                menu_item=self.item1 if i < 2 else self.item2,
                rating=4,
                comment=f'Review number {i+1} with consistent rating of four stars.'
            )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 4.0)
    
    def test_multiple_reviews_different_ratings(self):
        """Test average rating calculation with varying ratings."""
        # Create reviews with ratings: 5, 4, 3
        # Expected average: (5 + 4 + 3) / 3 = 4.0
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=5,
            comment='Absolutely perfect! Would definitely recommend this.'
        )
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.item1,
            rating=4,
            comment='Very good experience overall, will come back again.'
        )
        UserReview.objects.create(
            user=self.user3,
            menu_item=self.item2,
            rating=3,
            comment='It was okay, nothing special but not bad either.'
        )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 4.0)
    
    def test_average_with_decimal_result(self):
        """Test that decimal averages are calculated correctly and rounded."""
        # Create reviews with ratings: 5, 4, 4
        # Expected average: (5 + 4 + 4) / 3 = 4.333... = 4.33 (rounded)
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=5,
            comment='Outstanding quality and service, highly recommended!'
        )
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.item1,
            rating=4,
            comment='Really good food, will definitely order again soon.'
        )
        UserReview.objects.create(
            user=self.user3,
            menu_item=self.item2,
            rating=4,
            comment='Good experience, met all of my expectations well.'
        )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 4.33)
    
    def test_filter_by_menu_item(self):
        """Test average rating for a specific menu item."""
        # Item1: ratings 5, 4 (average 4.5)
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=5,
            comment='Perfect pizza with excellent ingredients and taste!'
        )
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.item1,
            rating=4,
            comment='Very tasty pizza, would recommend to all friends.'
        )
        
        # Item2: rating 2
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item2,
            rating=2,
            comment='Not great, the pasta was overcooked and bland.'
        )
        
        # Test item1 average
        item1_reviews = UserReview.objects.filter(menu_item=self.item1)
        average = calculate_average_rating(item1_reviews)
        self.assertEqual(average, 4.5)
        
        # Test item2 average
        item2_reviews = UserReview.objects.filter(menu_item=self.item2)
        average = calculate_average_rating(item2_reviews)
        self.assertEqual(average, 2.0)
    
    def test_filter_by_user(self):
        """Test average rating for reviews by a specific user."""
        # User1 gives: 5, 4 (average 4.5)
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=5,
            comment='Amazing experience with exceptional quality!'
        )
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item2,
            rating=4,
            comment='Very good overall, exceeded my expectations.'
        )
        
        # User2 gives: 3
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.item1,
            rating=3,
            comment='Average food, nothing particularly memorable.'
        )
        
        user1_reviews = UserReview.objects.filter(user=self.user1)
        average = calculate_average_rating(user1_reviews)
        self.assertEqual(average, 4.5)
    
    def test_all_rating_values(self):
        """Test average with all possible rating values (1-5)."""
        # Create reviews with ratings 1, 2, 3, 4, 5
        # Expected average: (1 + 2 + 3 + 4 + 5) / 5 = 3.0
        
        # Create additional menu items to avoid unique constraint
        item3 = MenuItem.objects.create(
            name='Salad',
            price='9.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        item4 = MenuItem.objects.create(
            name='Burger',
            price='11.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        ratings = [1, 2, 3, 4, 5]
        users = [self.user1, self.user2, self.user3, self.user1, self.user2]
        items = [self.item1, self.item1, self.item2, item3, item4]
        
        for i, rating in enumerate(ratings):
            UserReview.objects.create(
                user=users[i],
                menu_item=items[i],
                rating=rating,
                comment=f'Review with rating {rating} stars for testing purposes.'
            )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 3.0)
    
    def test_minimum_rating_only(self):
        """Test average when all reviews are minimum rating (1)."""
        for i in range(3):
            UserReview.objects.create(
                user=self.user1 if i == 0 else (self.user2 if i == 1 else self.user3),
                menu_item=self.item1 if i < 2 else self.item2,
                rating=1,
                comment=f'Poor experience number {i+1}, very disappointed.'
            )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 1.0)
    
    def test_maximum_rating_only(self):
        """Test average when all reviews are maximum rating (5)."""
        for i in range(3):
            UserReview.objects.create(
                user=self.user1 if i == 0 else (self.user2 if i == 1 else self.user3),
                menu_item=self.item1 if i < 2 else self.item2,
                rating=5,
                comment=f'Perfect experience {i+1}! Absolutely outstanding!'
            )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 5.0)
    
    def test_large_number_of_reviews(self):
        """Test average calculation with many reviews."""
        # Create 20 reviews: 10 with rating 5, 10 with rating 3
        # Expected average: (10*5 + 10*3) / 20 = 80/20 = 4.0
        
        # Create additional menu items for unique user/item combinations
        additional_items = []
        for i in range(18):
            item = MenuItem.objects.create(
                name=f'Item {i}',
                price='10.99',
                restaurant=self.restaurant,
                category=self.category,
                is_available=True
            )
            additional_items.append(item)
        
        # Use alternating users and items
        all_items = [self.item1, self.item2] + additional_items
        users = [self.user1, self.user2, self.user3]
        
        for i in range(20):
            rating = 5 if i < 10 else 3
            UserReview.objects.create(
                user=users[i % 3],
                menu_item=all_items[i],
                rating=rating,
                comment=f'Review {i+1} with rating {rating} for testing.'
            )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 4.0)
    
    def test_rounding_precision(self):
        """Test that rounding to 2 decimal places works correctly."""
        # Create reviews: 5, 3, 3
        # Expected: (5 + 3 + 3) / 3 = 3.666... = 3.67 (rounded)
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=5,
            comment='Excellent quality, would highly recommend to everyone!'
        )
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.item1,
            rating=3,
            comment='It was okay, met basic expectations but nothing more.'
        )
        UserReview.objects.create(
            user=self.user3,
            menu_item=self.item2,
            rating=3,
            comment='Average experience, nothing particularly stood out.'
        )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertEqual(average, 3.67)
        
        # Verify it's rounded to exactly 2 decimal places
        self.assertEqual(len(str(average).split('.')[-1]), 2)
    
    def test_return_type_is_float(self):
        """Test that the function always returns a float."""
        # Test with integer average
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=4,
            comment='Good experience overall, met my expectations well.'
        )
        
        reviews = UserReview.objects.all()
        average = calculate_average_rating(reviews)
        
        self.assertIsInstance(average, float)
        self.assertEqual(average, 4.0)
    
    def test_queryset_with_exclude(self):
        """Test that filtered querysets work correctly."""
        # Create reviews with different ratings
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.item1,
            rating=5,
            comment='Perfect pizza, absolutely loved it so much!'
        )
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.item1,
            rating=2,
            comment='Not good at all, very disappointed with quality.'
        )
        UserReview.objects.create(
            user=self.user3,
            menu_item=self.item2,
            rating=4,
            comment='Very good pasta, would definitely order again.'
        )
        
        # Exclude low ratings (< 4)
        high_rated_reviews = UserReview.objects.filter(rating__gte=4)
        average = calculate_average_rating(high_rated_reviews)
        
        # Average of 5 and 4 = 4.5
        self.assertEqual(average, 4.5)
