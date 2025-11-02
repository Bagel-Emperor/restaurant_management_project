"""
Test cases for LoyaltyProgram model enhancements.

This test module provides comprehensive coverage for the newly added fields
to the LoyaltyProgram model: points_per_dollar_spent and is_active.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from orders.models import LoyaltyProgram
from decimal import Decimal


class LoyaltyProgramPointsPerDollarSpentTests(TestCase):
    """Test cases for the points_per_dollar_spent field."""
    
    def test_default_points_per_dollar_spent(self):
        """Test that points_per_dollar_spent defaults to 1.0."""
        program = LoyaltyProgram.objects.create(
            name='Bronze Tier',
            points_required=0,
            discount_percentage=Decimal('5.00'),
            description='Entry level tier'
        )
        
        self.assertEqual(program.points_per_dollar_spent, Decimal('1.0'))
    
    def test_custom_points_per_dollar_spent(self):
        """Test setting a custom points_per_dollar_spent value."""
        program = LoyaltyProgram.objects.create(
            name='Gold Tier',
            points_required=1000,
            points_per_dollar_spent=Decimal('1.5'),
            discount_percentage=Decimal('15.00'),
            description='Premium tier earns 50% more points'
        )
        
        self.assertEqual(program.points_per_dollar_spent, Decimal('1.5'))
    
    def test_decimal_precision_points_per_dollar(self):
        """Test that points_per_dollar_spent stores decimal values correctly."""
        program = LoyaltyProgram.objects.create(
            name='Silver Tier',
            points_required=500,
            points_per_dollar_spent=Decimal('1.25'),
            discount_percentage=Decimal('10.00'),
            description='Mid-tier program'
        )
        
        self.assertEqual(program.points_per_dollar_spent, Decimal('1.25'))
    
    def test_zero_points_per_dollar_allowed(self):
        """Test that zero points_per_dollar_spent is allowed (non-earning tier)."""
        program = LoyaltyProgram.objects.create(
            name='Trial Tier',
            points_required=0,
            points_per_dollar_spent=Decimal('0.0'),
            discount_percentage=Decimal('0.00'),
            description='Trial tier with no earning'
        )
        
        self.assertEqual(program.points_per_dollar_spent, Decimal('0.0'))
        program.full_clean()  # Should not raise ValidationError
    
    def test_negative_points_per_dollar_rejected(self):
        """Test that negative points_per_dollar_spent is rejected by validator."""
        program = LoyaltyProgram(
            name='Invalid Tier',
            points_required=100,
            points_per_dollar_spent=Decimal('-1.0'),
            discount_percentage=Decimal('5.00'),
            description='Invalid negative earning rate'
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('points_per_dollar_spent', context.exception.message_dict)
    
    def test_high_points_per_dollar_value(self):
        """Test that high points_per_dollar_spent values are accepted."""
        program = LoyaltyProgram.objects.create(
            name='Platinum Tier',
            points_required=5000,
            points_per_dollar_spent=Decimal('5.0'),
            discount_percentage=Decimal('25.00'),
            description='Elite tier earns 5x points'
        )
        
        self.assertEqual(program.points_per_dollar_spent, Decimal('5.0'))
    
    def test_max_digits_and_decimal_places(self):
        """Test that points_per_dollar_spent respects max_digits=5 and decimal_places=2."""
        # Maximum value: 999.99
        program = LoyaltyProgram.objects.create(
            name='Super Platinum',
            points_required=10000,
            points_per_dollar_spent=Decimal('999.99'),
            discount_percentage=Decimal('30.00'),
            description='Maximum earning rate tier'
        )
        
        self.assertEqual(program.points_per_dollar_spent, Decimal('999.99'))
    
    def test_points_calculation_scenario(self):
        """Test realistic points earning calculation scenario."""
        # Gold tier: earn 1.5 points per dollar
        gold_tier = LoyaltyProgram.objects.create(
            name='Gold Member',
            points_required=1000,
            points_per_dollar_spent=Decimal('1.5'),
            discount_percentage=Decimal('15.00'),
            description='Gold tier benefits'
        )
        
        # Simulate a $100 purchase
        purchase_amount = Decimal('100.00')
        points_earned = purchase_amount * gold_tier.points_per_dollar_spent
        
        self.assertEqual(points_earned, Decimal('150.00'))


class LoyaltyProgramIsActiveTests(TestCase):
    """Test cases for the is_active field."""
    
    def test_default_is_active_true(self):
        """Test that is_active defaults to True."""
        program = LoyaltyProgram.objects.create(
            name='Bronze Tier',
            points_required=0,
            discount_percentage=Decimal('5.00'),
            description='Entry level tier'
        )
        
        self.assertTrue(program.is_active)
    
    def test_set_is_active_false(self):
        """Test setting is_active to False (deactivate program)."""
        program = LoyaltyProgram.objects.create(
            name='Deprecated Tier',
            points_required=250,
            discount_percentage=Decimal('8.00'),
            description='Old tier being phased out',
            is_active=False
        )
        
        self.assertFalse(program.is_active)
    
    def test_toggle_is_active(self):
        """Test toggling is_active status."""
        program = LoyaltyProgram.objects.create(
            name='Silver Tier',
            points_required=500,
            discount_percentage=Decimal('10.00'),
            description='Mid-tier program'
        )
        
        # Initially active
        self.assertTrue(program.is_active)
        
        # Deactivate
        program.is_active = False
        program.save()
        program.refresh_from_db()
        self.assertFalse(program.is_active)
        
        # Reactivate
        program.is_active = True
        program.save()
        program.refresh_from_db()
        self.assertTrue(program.is_active)
    
    def test_filter_active_programs(self):
        """Test filtering to get only active loyalty programs."""
        # Create mix of active and inactive programs
        LoyaltyProgram.objects.create(
            name='Bronze',
            points_required=0,
            discount_percentage=Decimal('5.00'),
            description='Active bronze',
            is_active=True
        )
        
        LoyaltyProgram.objects.create(
            name='Silver',
            points_required=500,
            discount_percentage=Decimal('10.00'),
            description='Active silver',
            is_active=True
        )
        
        LoyaltyProgram.objects.create(
            name='Old Gold',
            points_required=1000,
            discount_percentage=Decimal('15.00'),
            description='Inactive old tier',
            is_active=False
        )
        
        active_programs = LoyaltyProgram.objects.filter(is_active=True)
        inactive_programs = LoyaltyProgram.objects.filter(is_active=False)
        
        self.assertEqual(active_programs.count(), 2)
        self.assertEqual(inactive_programs.count(), 1)
    
    def test_is_active_boolean_field_type(self):
        """Test that is_active is a proper BooleanField."""
        program = LoyaltyProgram.objects.create(
            name='Test Tier',
            points_required=100,
            discount_percentage=Decimal('7.00'),
            description='Test program'
        )
        
        # Should be boolean, not string or int
        self.assertIsInstance(program.is_active, bool)
        self.assertIn(program.is_active, [True, False])


class LoyaltyProgramCombinedFieldsTests(TestCase):
    """Test cases for interactions between all LoyaltyProgram fields."""
    
    def test_complete_program_with_all_fields(self):
        """Test creating a complete loyalty program with all fields."""
        program = LoyaltyProgram.objects.create(
            name='Platinum Member',
            points_required=2500,
            points_per_dollar_spent=Decimal('2.0'),
            discount_percentage=Decimal('20.00'),
            description='Elite platinum tier with double points and 20% discount',
            is_active=True
        )
        
        self.assertEqual(program.name, 'Platinum Member')
        self.assertEqual(program.points_required, 2500)
        self.assertEqual(program.points_per_dollar_spent, Decimal('2.0'))
        self.assertEqual(program.discount_percentage, Decimal('20.00'))
        self.assertEqual(program.description, 'Elite platinum tier with double points and 20% discount')
        self.assertTrue(program.is_active)
        self.assertIsNotNone(program.created_at)
        self.assertIsNotNone(program.updated_at)
    
    def test_inactive_program_still_has_earning_rate(self):
        """Test that inactive programs still maintain their earning rate data."""
        program = LoyaltyProgram.objects.create(
            name='Retired Gold',
            points_required=1500,
            points_per_dollar_spent=Decimal('1.75'),
            discount_percentage=Decimal('17.50'),
            description='Retired tier',
            is_active=False
        )
        
        # Even though inactive, data is preserved
        self.assertFalse(program.is_active)
        self.assertEqual(program.points_per_dollar_spent, Decimal('1.75'))
        self.assertEqual(program.discount_percentage, Decimal('17.50'))
    
    def test_different_tiers_different_earning_rates(self):
        """Test that different tiers can have different earning rates."""
        bronze = LoyaltyProgram.objects.create(
            name='Bronze',
            points_required=0,
            points_per_dollar_spent=Decimal('1.0'),
            discount_percentage=Decimal('5.00'),
            description='Bronze tier'
        )
        
        silver = LoyaltyProgram.objects.create(
            name='Silver',
            points_required=500,
            points_per_dollar_spent=Decimal('1.25'),
            discount_percentage=Decimal('10.00'),
            description='Silver tier'
        )
        
        gold = LoyaltyProgram.objects.create(
            name='Gold',
            points_required=1000,
            points_per_dollar_spent=Decimal('1.5'),
            discount_percentage=Decimal('15.00'),
            description='Gold tier'
        )
        
        # Verify earning rates increase with tier level
        self.assertLess(bronze.points_per_dollar_spent, silver.points_per_dollar_spent)
        self.assertLess(silver.points_per_dollar_spent, gold.points_per_dollar_spent)
    
    def test_updated_at_changes_on_field_modification(self):
        """Test that updated_at changes when fields are modified."""
        import time
        
        program = LoyaltyProgram.objects.create(
            name='Dynamic Tier',
            points_required=750,
            points_per_dollar_spent=Decimal('1.3'),
            discount_percentage=Decimal('12.00'),
            description='Original description'
        )
        
        original_updated_at = program.updated_at
        
        # Wait and update fields
        time.sleep(0.01)
        program.points_per_dollar_spent = Decimal('1.5')
        program.is_active = False
        program.save()
        
        program.refresh_from_db()
        self.assertGreater(program.updated_at, original_updated_at)
    
    def test_str_representation_unchanged(self):
        """Test that __str__ representation still works with new fields."""
        program = LoyaltyProgram.objects.create(
            name='Test Tier',
            points_required=300,
            points_per_dollar_spent=Decimal('1.2'),
            discount_percentage=Decimal('9.00'),
            description='Test tier'
        )
        
        expected_str = "Test Tier (300 points - 9.00% discount)"
        self.assertEqual(str(program), expected_str)
    
    def test_ordering_still_by_points_required(self):
        """Test that model ordering is still by points_required."""
        # Create tiers in non-sorted order
        gold = LoyaltyProgram.objects.create(
            name='Gold',
            points_required=1000,
            points_per_dollar_spent=Decimal('1.5'),
            discount_percentage=Decimal('15.00'),
            description='Gold tier'
        )
        
        bronze = LoyaltyProgram.objects.create(
            name='Bronze',
            points_required=0,
            points_per_dollar_spent=Decimal('1.0'),
            discount_percentage=Decimal('5.00'),
            description='Bronze tier'
        )
        
        silver = LoyaltyProgram.objects.create(
            name='Silver',
            points_required=500,
            points_per_dollar_spent=Decimal('1.25'),
            discount_percentage=Decimal('10.00'),
            description='Silver tier'
        )
        
        # Get all in default order
        all_programs = list(LoyaltyProgram.objects.all())
        
        # Should be ordered by points_required
        self.assertEqual(all_programs[0], bronze)
        self.assertEqual(all_programs[1], silver)
        self.assertEqual(all_programs[2], gold)


class LoyaltyProgramBackwardsCompatibilityTests(TestCase):
    """Test that existing functionality still works with new fields."""
    
    def test_existing_tests_still_pass(self):
        """Test that existing LoyaltyProgram functionality still works."""
        # Test unique constraints still work
        LoyaltyProgram.objects.create(
            name='Unique Name',
            points_required=100,
            discount_percentage=Decimal('5.00'),
            description='Test'
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            LoyaltyProgram.objects.create(
                name='Unique Name',  # Duplicate name
                points_required=200,
                discount_percentage=Decimal('10.00'),
                description='Test'
            )
    
    def test_validators_still_work(self):
        """Test that existing validators still work."""
        # Negative points_required should still be rejected
        program = LoyaltyProgram(
            name='Invalid',
            points_required=-100,
            discount_percentage=Decimal('5.00'),
            description='Test'
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('points_required', context.exception.message_dict)
    
    def test_discount_percentage_validators_still_work(self):
        """Test that discount_percentage validators (0-100) still work."""
        # Over 100% discount should be rejected
        program = LoyaltyProgram(
            name='Invalid Discount',
            points_required=500,
            discount_percentage=Decimal('150.00'),
            description='Test'
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('discount_percentage', context.exception.message_dict)
