from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from home.models import UserReview, MenuItem, Restaurant, MenuCategory
from decimal import Decimal


class UserReviewModelTest(TestCase):
	"""Test suite for the UserReview model"""
	
	def setUp(self):
		"""Set up test data"""
		# Create a test user
		self.user = User.objects.create_user(username='testuser', password='testpass123')
		
		# Create a test restaurant
		self.restaurant = Restaurant.objects.create(
			name='Test Restaurant',
			owner_name='Test Owner',
			email='test@restaurant.com',
			phone_number='1234567890'
		)
		
		# Create a test category
		self.category = MenuCategory.objects.create(name='Appetizers')
		
		# Create a test menu item
		self.menu_item = MenuItem.objects.create(
			name='Test Burger',
			description='A delicious test burger',
			price=Decimal('12.99'),
			restaurant=self.restaurant,
			category=self.category
		)
	
	def test_create_valid_review(self):
		"""Test creating a valid review"""
		review = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='Excellent burger!'
		)
		
		self.assertEqual(review.user, self.user)
		self.assertEqual(review.menu_item, self.menu_item)
		self.assertEqual(review.rating, 5)
		self.assertEqual(review.comment, 'Excellent burger!')
		self.assertIsNotNone(review.review_date)
	
	def test_review_string_representation(self):
		"""Test the string representation of a review"""
		review = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=4,
			comment='Good burger'
		)
		
		expected_str = f"{self.user.username}'s review of {self.menu_item.name} - 4/5"
		self.assertEqual(str(review), expected_str)
	
	def test_review_date_auto_added(self):
		"""Test that review_date is automatically set"""
		review = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=3,
			comment='Average burger'
		)
		
		self.assertIsNotNone(review.review_date)
	
	def test_rating_validation_too_low(self):
		"""Test that rating below 1 is invalid"""
		review = UserReview(
			user=self.user,
			menu_item=self.menu_item,
			rating=0,
			comment='Bad rating'
		)
		
		with self.assertRaises(ValidationError):
			review.full_clean()
	
	def test_rating_validation_too_high(self):
		"""Test that rating above 5 is invalid"""
		review = UserReview(
			user=self.user,
			menu_item=self.menu_item,
			rating=6,
			comment='Too high rating'
		)
		
		with self.assertRaises(ValidationError):
			review.full_clean()
	
	def test_rating_validation_valid_range(self):
		"""Test that ratings 1-5 are valid"""
		for rating in range(1, 6):
			review = UserReview(
				user=self.user,
				menu_item=self.menu_item,
				rating=rating,
				comment=f'Rating {rating}'
			)
			# Should not raise ValidationError
			review.full_clean()
	
	def test_unique_user_menu_item_constraint(self):
		"""Test that a user can only review a menu item once"""
		# Create first review
		UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='First review'
		)
		
		# Try to create second review for same user and menu item
		with self.assertRaises(Exception):  # Will raise IntegrityError
			UserReview.objects.create(
				user=self.user,
				menu_item=self.menu_item,
				rating=4,
				comment='Second review'
			)
	
	def test_multiple_users_can_review_same_item(self):
		"""Test that multiple users can review the same menu item"""
		user2 = User.objects.create_user(username='testuser2', password='testpass123')
		
		review1 = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='User 1 review'
		)
		
		review2 = UserReview.objects.create(
			user=user2,
			menu_item=self.menu_item,
			rating=3,
			comment='User 2 review'
		)
		
		self.assertEqual(UserReview.objects.filter(menu_item=self.menu_item).count(), 2)
	
	def test_user_can_review_multiple_items(self):
		"""Test that a user can review multiple menu items"""
		menu_item2 = MenuItem.objects.create(
			name='Test Pizza',
			description='A delicious test pizza',
			price=Decimal('15.99'),
			restaurant=self.restaurant,
			category=self.category
		)
		
		review1 = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='Great burger'
		)
		
		review2 = UserReview.objects.create(
			user=self.user,
			menu_item=menu_item2,
			rating=4,
			comment='Good pizza'
		)
		
		self.assertEqual(UserReview.objects.filter(user=self.user).count(), 2)
	
	def test_review_ordering(self):
		"""Test that reviews are ordered by most recent first"""
		review1 = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='First review'
		)
		
		user2 = User.objects.create_user(username='testuser2', password='testpass123')
		review2 = UserReview.objects.create(
			user=user2,
			menu_item=self.menu_item,
			rating=4,
			comment='Second review'
		)
		
		reviews = list(UserReview.objects.all())
		# Most recent should be first
		self.assertEqual(reviews[0], review2)
		self.assertEqual(reviews[1], review1)
	
	def test_cascade_delete_user(self):
		"""Test that deleting a user deletes their reviews"""
		review = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='Test review'
		)
		
		review_id = review.id
		self.user.delete()
		
		# Review should be deleted
		self.assertFalse(UserReview.objects.filter(id=review_id).exists())
	
	def test_cascade_delete_menu_item(self):
		"""Test that deleting a menu item deletes its reviews"""
		review = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='Test review'
		)
		
		review_id = review.id
		self.menu_item.delete()
		
		# Review should be deleted
		self.assertFalse(UserReview.objects.filter(id=review_id).exists())
	
	def test_related_name_reviews_on_user(self):
		"""Test accessing reviews through user's related_name"""
		review = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='Test review'
		)
		
		user_reviews = self.user.reviews.all()
		self.assertEqual(user_reviews.count(), 1)
		self.assertEqual(user_reviews.first(), review)
	
	def test_related_name_reviews_on_menu_item(self):
		"""Test accessing reviews through menu_item's related_name"""
		review = UserReview.objects.create(
			user=self.user,
			menu_item=self.menu_item,
			rating=5,
			comment='Test review'
		)
		
		item_reviews = self.menu_item.reviews.all()
		self.assertEqual(item_reviews.count(), 1)
		self.assertEqual(item_reviews.first(), review)
