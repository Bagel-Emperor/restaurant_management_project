from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from home.models import UserReview, MenuItem, Restaurant, MenuCategory
from decimal import Decimal


class UserReviewAPITest(TestCase):
    """Test suite for the User Review API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', password='testpass123')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass123')
        
        # Create a test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='1234567890'
        )
        
        # Create a test category
        self.category = MenuCategory.objects.create(name='Main Courses')
        
        # Create test menu items
        self.menu_item1 = MenuItem.objects.create(
            name='Test Burger',
            description='A delicious test burger',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.menu_item2 = MenuItem.objects.create(
            name='Test Pizza',
            description='A delicious test pizza',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.unavailable_item = MenuItem.objects.create(
            name='Unavailable Item',
            description='Not available',
            price=Decimal('10.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=False
        )
        
        # Create a test review
        self.existing_review = UserReview.objects.create(
            user=self.user1,
            menu_item=self.menu_item1,
            rating=5,
            comment='Excellent burger!'
        )
    
    def test_list_reviews_public_access(self):
        """Test that anyone can list reviews without authentication"""
        response = self.client.get('/PerpexBistro/api/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_review_public_access(self):
        """Test that anyone can retrieve a single review without authentication"""
        response = self.client.get(f'/PerpexBistro/api/reviews/{self.existing_review.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.existing_review.id)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['user_username'], 'testuser1')
        self.assertEqual(response.data['menu_item_name'], 'Test Burger')
    
    def test_create_review_requires_authentication(self):
        """Test that creating a review requires authentication"""
        data = {
            'menu_item': self.menu_item2.id,
            'rating': 4,
            'comment': 'Good pizza but could be better'
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_review_authenticated(self):
        """Test creating a review when authenticated"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'menu_item': self.menu_item2.id,
            'rating': 4,
            'comment': 'Good pizza but could be better with more cheese'
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 4)
        self.assertEqual(response.data['user_username'], 'testuser1')
        self.assertEqual(response.data['menu_item_name'], 'Test Pizza')
        self.assertIn('review_date', response.data)
        
        # Verify review was created in database
        self.assertTrue(UserReview.objects.filter(
            user=self.user1,
            menu_item=self.menu_item2
        ).exists())
    
    def test_create_review_duplicate_prevention(self):
        """Test that a user cannot review the same menu item twice"""
        self.client.force_authenticate(user=self.user1)
        
        # Try to create another review for menu_item1 (already reviewed)
        data = {
            'menu_item': self.menu_item1.id,
            'rating': 3,
            'comment': 'Changed my mind, not that great anymore'
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already reviewed', str(response.data).lower())
    
    def test_create_review_invalid_rating_too_low(self):
        """Test that rating below 1 is rejected"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'menu_item': self.menu_item2.id,
            'rating': 0,
            'comment': 'Terrible experience'
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rating', str(response.data).lower())
    
    def test_create_review_invalid_rating_too_high(self):
        """Test that rating above 5 is rejected"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'menu_item': self.menu_item2.id,
            'rating': 6,
            'comment': 'Beyond excellent!'
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rating', str(response.data).lower())
    
    def test_create_review_comment_too_short(self):
        """Test that comment must be at least 10 characters"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'menu_item': self.menu_item2.id,
            'rating': 4,
            'comment': 'Good'
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('comment', str(response.data).lower())
    
    def test_create_review_empty_comment(self):
        """Test that comment cannot be empty"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'menu_item': self.menu_item2.id,
            'rating': 4,
            'comment': ''
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_review_unavailable_menu_item(self):
        """Test that cannot review unavailable menu item"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'menu_item': self.unavailable_item.id,
            'rating': 3,
            'comment': 'Trying to review unavailable item'
        }
        
        response = self.client.post('/PerpexBistro/api/reviews/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unavailable', str(response.data).lower())
    
    def test_update_own_review(self):
        """Test that users can update their own reviews"""
        self.client.force_authenticate(user=self.user1)
        
        data = {
            'rating': 4,
            'comment': 'Updated: Still good but not perfect'
        }
        
        response = self.client.patch(f'/PerpexBistro/api/reviews/{self.existing_review.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 4)
        self.assertIn('Updated', response.data['comment'])
        
        # Verify in database
        self.existing_review.refresh_from_db()
        self.assertEqual(self.existing_review.rating, 4)
    
    def test_update_other_user_review_forbidden(self):
        """Test that users cannot update other users' reviews"""
        self.client.force_authenticate(user=self.user2)
        
        data = {
            'rating': 1,
            'comment': 'Trying to sabotage someone else\'s review'
        }
        
        response = self.client.patch(f'/PerpexBistro/api/reviews/{self.existing_review.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('own reviews', str(response.data).lower())
    
    def test_delete_own_review(self):
        """Test that users can delete their own reviews"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.delete(f'/PerpexBistro/api/reviews/{self.existing_review.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify deleted from database
        self.assertFalse(UserReview.objects.filter(id=self.existing_review.id).exists())
    
    def test_delete_other_user_review_forbidden(self):
        """Test that users cannot delete other users' reviews"""
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.delete(f'/PerpexBistro/api/reviews/{self.existing_review.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('own reviews', str(response.data).lower())
        
        # Verify not deleted
        self.assertTrue(UserReview.objects.filter(id=self.existing_review.id).exists())
    
    def test_filter_reviews_by_menu_item(self):
        """Test filtering reviews by menu_item"""
        # Create another review for a different menu item
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.menu_item2,
            rating=4,
            comment='Great pizza with excellent crust'
        )
        
        response = self.client.get(f'/PerpexBistro/api/reviews/?menu_item={self.menu_item1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['menu_item'], self.menu_item1.id)
    
    def test_filter_reviews_by_rating(self):
        """Test filtering reviews by rating"""
        # Create reviews with different ratings
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.menu_item2,
            rating=3,
            comment='Average pizza, nothing special'
        )
        
        response = self.client.get('/PerpexBistro/api/reviews/?rating=5')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['rating'], 5)
    
    def test_filter_reviews_by_user(self):
        """Test filtering reviews by user"""
        # Create another review by user2
        UserReview.objects.create(
            user=self.user2,
            menu_item=self.menu_item2,
            rating=4,
            comment='Pretty good pizza overall'
        )
        
        response = self.client.get(f'/PerpexBistro/api/reviews/?user={self.user1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user'], self.user1.id)
    
    def test_my_reviews_endpoint(self):
        """Test the my_reviews custom action"""
        # Create another review by user1
        UserReview.objects.create(
            user=self.user1,
            menu_item=self.menu_item2,
            rating=4,
            comment='Good pizza but not as good as the burger'
        )
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/PerpexBistro/api/reviews/my_reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        # All reviews should belong to user1
        for review in response.data['results']:
            self.assertEqual(review['user'], self.user1.id)
    
    def test_my_reviews_requires_authentication(self):
        """Test that my_reviews requires authentication"""
        response = self.client.get('/PerpexBistro/api/reviews/my_reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_reviews_ordered_by_date(self):
        """Test that reviews are ordered by most recent first"""
        # Create additional reviews
        review2 = UserReview.objects.create(
            user=self.user2,
            menu_item=self.menu_item2,
            rating=4,
            comment='Good pizza with nice toppings'
        )
        
        response = self.client.get('/PerpexBistro/api/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Most recent should be first
        self.assertEqual(response.data['results'][0]['id'], review2.id)
        self.assertEqual(response.data['results'][1]['id'], self.existing_review.id)
    
    def test_create_review_all_valid_ratings(self):
        """Test creating reviews with all valid ratings (1-5)"""
        self.client.force_authenticate(user=self.user2)
        
        menu_items = [self.menu_item1, self.menu_item2]
        
        for rating in range(1, 6):
            if rating <= len(menu_items):
                data = {
                    'menu_item': menu_items[rating - 1].id,
                    'rating': rating,
                    'comment': f'Test review with {rating} star rating'
                }
                
                response = self.client.post('/PerpexBistro/api/reviews/', data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data['rating'], rating)
