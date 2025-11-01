"""
Test suite for the LoyaltyProgram model.

This module tests the LoyaltyProgram model defined in orders/models.py,
ensuring proper field validation, unique constraints, and functionality
for customer loyalty tier management.
"""

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from decimal import Decimal
from orders.models import LoyaltyProgram


class LoyaltyProgramModelTest(TestCase):
    """Test cases for the LoyaltyProgram model."""
    
    def setUp(self):
        """Set up test data before each test."""
        # Create sample loyalty programs
        self.bronze_tier = LoyaltyProgram.objects.create(
            name='Bronze Member',
            points_required=0,
            discount_percentage=Decimal('5.00'),
            description='Entry level tier with 5% discount on all orders'
        )
        self.silver_tier = LoyaltyProgram.objects.create(
            name='Silver Member',
            points_required=100,
            discount_percentage=Decimal('10.00'),
            description='Mid-level tier with 10% discount and priority support'
        )
        self.gold_tier = LoyaltyProgram.objects.create(
            name='Gold Member',
            points_required=500,
            discount_percentage=Decimal('15.00'),
            description='Premium tier with 15% discount and exclusive perks'
        )
    
    def test_create_loyalty_program_with_all_fields(self):
        """Test creating a loyalty program with all required fields."""
        platinum_tier = LoyaltyProgram.objects.create(
            name='Platinum Member',
            points_required=1000,
            discount_percentage=Decimal('20.00'),
            description='Elite tier with 20% discount and VIP benefits'
        )
        
        self.assertEqual(platinum_tier.name, 'Platinum Member')
        self.assertEqual(platinum_tier.points_required, 1000)
        self.assertEqual(platinum_tier.discount_percentage, Decimal('20.00'))
        self.assertEqual(platinum_tier.description, 'Elite tier with 20% discount and VIP benefits')
        self.assertIsNotNone(platinum_tier.created_at)
        self.assertIsNotNone(platinum_tier.updated_at)
    
    def test_loyalty_program_str_representation(self):
        """Test the string representation of a LoyaltyProgram."""
        expected = "Bronze Member (0 points - 5.00% discount)"
        self.assertEqual(str(self.bronze_tier), expected)
        
        expected = "Silver Member (100 points - 10.00% discount)"
        self.assertEqual(str(self.silver_tier), expected)
    
    def test_name_field_max_length(self):
        """Test that name field respects max_length constraint."""
        long_name = 'A' * 51  # 51 characters (exceeds max_length of 50)
        
        tier = LoyaltyProgram(
            name=long_name,
            points_required=2000,
            discount_percentage=Decimal('25.00'),
            description='Test tier'
        )
        
        with self.assertRaises(ValidationError):
            tier.full_clean()
    
    def test_name_field_is_unique(self):
        """Test that name field must be unique."""
        with self.assertRaises(IntegrityError):
            LoyaltyProgram.objects.create(
                name='Bronze Member',  # Duplicate name
                points_required=50,
                discount_percentage=Decimal('7.50'),
                description='Duplicate bronze tier'
            )
    
    def test_points_required_is_unique(self):
        """Test that points_required field must be unique."""
        with self.assertRaises(IntegrityError):
            LoyaltyProgram.objects.create(
                name='Special Bronze',
                points_required=0,  # Duplicate points_required
                discount_percentage=Decimal('6.00'),
                description='Another entry tier'
            )
    
    def test_discount_percentage_decimal_field(self):
        """Test that discount_percentage stores decimal values correctly."""
        tier = LoyaltyProgram.objects.create(
            name='Test Tier',
            points_required=250,
            discount_percentage=Decimal('12.50'),
            description='Test tier with decimal discount'
        )
        
        self.assertEqual(tier.discount_percentage, Decimal('12.50'))
        self.assertIsInstance(tier.discount_percentage, Decimal)
    
    def test_discount_percentage_with_two_decimal_places(self):
        """Test that discount_percentage accepts values with two decimal places."""
        tier = LoyaltyProgram.objects.create(
            name='Precise Discount Tier',
            points_required=750,
            discount_percentage=Decimal('17.75'),
            description='Tier with precise discount percentage'
        )
        
        self.assertEqual(tier.discount_percentage, Decimal('17.75'))
    
    def test_description_text_field(self):
        """Test that description field can store long text."""
        long_description = "This is a very detailed description of the loyalty program tier. " * 20
        
        tier = LoyaltyProgram.objects.create(
            name='Descriptive Tier',
            points_required=1500,
            discount_percentage=Decimal('22.00'),
            description=long_description
        )
        
        self.assertEqual(tier.description, long_description)
    
    def test_ordering_by_points_required(self):
        """Test that loyalty programs are ordered by points_required."""
        all_tiers = list(LoyaltyProgram.objects.all())
        
        # Should be ordered: Bronze (0), Silver (100), Gold (500)
        self.assertEqual(all_tiers[0].name, 'Bronze Member')
        self.assertEqual(all_tiers[1].name, 'Silver Member')
        self.assertEqual(all_tiers[2].name, 'Gold Member')
        
        # Verify points are in ascending order
        for i in range(len(all_tiers) - 1):
            self.assertLessEqual(
                all_tiers[i].points_required,
                all_tiers[i + 1].points_required
            )
    
    def test_created_at_auto_now_add(self):
        """Test that created_at is automatically set on creation."""
        tier = LoyaltyProgram.objects.create(
            name='Time Test Tier',
            points_required=300,
            discount_percentage=Decimal('11.00'),
            description='Testing timestamps'
        )
        
        self.assertIsNotNone(tier.created_at)
    
    def test_updated_at_auto_now(self):
        """Test that updated_at is automatically updated on save."""
        tier = LoyaltyProgram.objects.create(
            name='Update Test Tier',
            points_required=400,
            discount_percentage=Decimal('13.00'),
            description='Testing update timestamps'
        )
        
        original_updated_at = tier.updated_at
        
        # Update the tier
        tier.discount_percentage = Decimal('14.00')
        tier.save()
        
        # Refresh from database
        tier.refresh_from_db()
        
        # updated_at should have changed
        self.assertGreater(tier.updated_at, original_updated_at)
    
    def test_zero_points_required(self):
        """Test that points_required can be zero for entry-level tiers."""
        # Bronze tier already has 0 points
        self.assertEqual(self.bronze_tier.points_required, 0)
        self.assertIsNotNone(self.bronze_tier.id)
    
    def test_negative_points_required(self):
        """Test that negative points_required are rejected by validator."""
        tier = LoyaltyProgram(
            name='Negative Points Tier',
            points_required=-100,
            discount_percentage=Decimal('1.00'),
            description='Testing negative points'
        )
        
        with self.assertRaises(ValidationError) as context:
            tier.full_clean()
        
        # Check that the error is on the points_required field
        self.assertIn('points_required', context.exception.message_dict)
    
    def test_zero_discount_percentage(self):
        """Test that discount_percentage can be zero."""
        tier = LoyaltyProgram.objects.create(
            name='No Discount Tier',
            points_required=50,
            discount_percentage=Decimal('0.00'),
            description='Tier with no discount benefits'
        )
        
        self.assertEqual(tier.discount_percentage, Decimal('0.00'))
    
    def test_large_discount_percentage(self):
        """Test that discount_percentage above 100% is rejected by validator."""
        tier = LoyaltyProgram(
            name='Huge Discount Tier',
            points_required=5000,
            discount_percentage=Decimal('999.99'),
            description='Tier with maximum discount'
        )
        
        with self.assertRaises(ValidationError) as context:
            tier.full_clean()
        
        # Check that the error is on the discount_percentage field
        self.assertIn('discount_percentage', context.exception.message_dict)
    
    def test_discount_percentage_at_max_boundary(self):
        """Test that discount_percentage of exactly 100% is allowed."""
        tier = LoyaltyProgram.objects.create(
            name='Max Discount Tier',
            points_required=10000,
            discount_percentage=Decimal('100.00'),
            description='Tier with 100% discount (free items)'
        )
        
        self.assertEqual(tier.discount_percentage, Decimal('100.00'))
        tier.full_clean()  # Should not raise ValidationError
    
    def test_discount_percentage_above_100_boundary(self):
        """Test that discount_percentage just above 100% is rejected."""
        tier = LoyaltyProgram(
            name='Over 100 Discount Tier',
            points_required=15000,
            discount_percentage=Decimal('100.01'),
            description='Testing boundary'
        )
        
        with self.assertRaises(ValidationError) as context:
            tier.full_clean()
        
        self.assertIn('discount_percentage', context.exception.message_dict)
    
    def test_verbose_name(self):
        """Test the verbose_name is set correctly."""
        self.assertEqual(
            LoyaltyProgram._meta.verbose_name,
            "Loyalty Program"
        )
    
    def test_verbose_name_plural(self):
        """Test the verbose_name_plural is set correctly."""
        self.assertEqual(
            LoyaltyProgram._meta.verbose_name_plural,
            "Loyalty Programs"
        )
    
    def test_multiple_tiers_retrieval(self):
        """Test retrieving multiple loyalty program tiers."""
        all_tiers = LoyaltyProgram.objects.all()
        
        self.assertEqual(all_tiers.count(), 3)
        self.assertIn(self.bronze_tier, all_tiers)
        self.assertIn(self.silver_tier, all_tiers)
        self.assertIn(self.gold_tier, all_tiers)
    
    def test_filter_by_points_required(self):
        """Test filtering loyalty programs by points_required."""
        high_tiers = LoyaltyProgram.objects.filter(points_required__gte=100)
        
        self.assertEqual(high_tiers.count(), 2)
        self.assertIn(self.silver_tier, high_tiers)
        self.assertIn(self.gold_tier, high_tiers)
        self.assertNotIn(self.bronze_tier, high_tiers)
    
    def test_filter_by_discount_percentage(self):
        """Test filtering loyalty programs by discount_percentage."""
        premium_tiers = LoyaltyProgram.objects.filter(
            discount_percentage__gte=Decimal('10.00')
        )
        
        self.assertEqual(premium_tiers.count(), 2)
        self.assertIn(self.silver_tier, premium_tiers)
        self.assertIn(self.gold_tier, premium_tiers)
        self.assertNotIn(self.bronze_tier, premium_tiers)
    
    def test_update_loyalty_program(self):
        """Test updating a loyalty program's fields."""
        self.bronze_tier.discount_percentage = Decimal('6.00')
        self.bronze_tier.description = 'Updated bronze tier with 6% discount'
        self.bronze_tier.save()
        
        # Refresh from database
        self.bronze_tier.refresh_from_db()
        
        self.assertEqual(self.bronze_tier.discount_percentage, Decimal('6.00'))
        self.assertEqual(self.bronze_tier.description, 'Updated bronze tier with 6% discount')
    
    def test_delete_loyalty_program(self):
        """Test deleting a loyalty program."""
        tier_id = self.bronze_tier.id
        self.bronze_tier.delete()
        
        with self.assertRaises(LoyaltyProgram.DoesNotExist):
            LoyaltyProgram.objects.get(id=tier_id)
        
        # Verify count decreased
        self.assertEqual(LoyaltyProgram.objects.count(), 2)
    
    def test_get_or_create_loyalty_program(self):
        """Test get_or_create functionality."""
        # Try to get existing tier
        tier, created = LoyaltyProgram.objects.get_or_create(
            name='Bronze Member',
            defaults={
                'points_required': 0,
                'discount_percentage': Decimal('5.00'),
                'description': 'Entry level tier'
            }
        )
        
        self.assertFalse(created)
        self.assertEqual(tier.id, self.bronze_tier.id)
        
        # Create new tier
        new_tier, created = LoyaltyProgram.objects.get_or_create(
            name='Diamond Member',
            defaults={
                'points_required': 10000,
                'discount_percentage': Decimal('30.00'),
                'description': 'Ultimate tier'
            }
        )
        
        self.assertTrue(created)
        self.assertEqual(new_tier.name, 'Diamond Member')
