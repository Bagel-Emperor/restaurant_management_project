"""
Test cases for PaymentMethod model.

This test module provides comprehensive coverage for the PaymentMethod model,
including field validation, constraints, and behavior.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from orders.models import PaymentMethod


class PaymentMethodModelTests(TestCase):
    """Test cases for PaymentMethod model fields and constraints."""
    
    def test_create_payment_method_with_all_fields(self):
        """Test creating a payment method with all fields populated."""
        payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            description='Pay securely with Visa, Mastercard, or American Express',
            is_active=True
        )
        
        self.assertEqual(payment_method.name, 'Credit Card')
        self.assertEqual(payment_method.description, 'Pay securely with Visa, Mastercard, or American Express')
        self.assertTrue(payment_method.is_active)
    
    def test_create_payment_method_minimal_fields(self):
        """Test creating a payment method with only required fields."""
        payment_method = PaymentMethod.objects.create(
            name='Cash'
        )
        
        self.assertEqual(payment_method.name, 'Cash')
        self.assertIsNone(payment_method.description)
        self.assertTrue(payment_method.is_active)  # Default is True
    
    def test_default_is_active_true(self):
        """Test that is_active defaults to True."""
        payment_method = PaymentMethod.objects.create(name='PayPal')
        
        self.assertTrue(payment_method.is_active)
    
    def test_name_max_length(self):
        """Test that name field respects max_length of 50."""
        long_name = 'A' * 50
        payment_method = PaymentMethod.objects.create(name=long_name)
        
        self.assertEqual(len(payment_method.name), 50)
        self.assertEqual(payment_method.name, long_name)
    
    def test_name_exceeds_max_length(self):
        """Test that name exceeding 50 characters is rejected."""
        too_long_name = 'A' * 51
        payment_method = PaymentMethod(name=too_long_name)
        
        with self.assertRaises(ValidationError) as context:
            payment_method.full_clean()
        
        self.assertIn('name', context.exception.message_dict)
    
    def test_name_unique_constraint(self):
        """Test that name must be unique."""
        PaymentMethod.objects.create(name='Debit Card')
        
        with self.assertRaises(IntegrityError):
            PaymentMethod.objects.create(name='Debit Card')
    
    def test_name_case_sensitive_uniqueness(self):
        """Test that name uniqueness is case-sensitive in database."""
        PaymentMethod.objects.create(name='Credit Card')
        
        # Different case - should be allowed by database
        # (Though in practice, you might want case-insensitive uniqueness)
        payment_method = PaymentMethod.objects.create(name='credit card')
        self.assertEqual(payment_method.name, 'credit card')
    
    def test_description_can_be_blank(self):
        """Test that description field can be blank."""
        payment_method = PaymentMethod.objects.create(
            name='Gift Card',
            description=''
        )
        
        self.assertEqual(payment_method.description, '')
    
    def test_description_can_be_null(self):
        """Test that description field can be null."""
        payment_method = PaymentMethod.objects.create(
            name='Bank Transfer',
            description=None
        )
        
        self.assertIsNone(payment_method.description)
    
    def test_description_can_be_long_text(self):
        """Test that description can store long text."""
        long_description = 'A' * 500
        payment_method = PaymentMethod.objects.create(
            name='Apple Pay',
            description=long_description
        )
        
        self.assertEqual(len(payment_method.description), 500)
        self.assertEqual(payment_method.description, long_description)
    
    def test_is_active_can_be_false(self):
        """Test that is_active can be set to False."""
        payment_method = PaymentMethod.objects.create(
            name='Check',
            is_active=False
        )
        
        self.assertFalse(payment_method.is_active)
    
    def test_toggle_is_active(self):
        """Test toggling is_active status."""
        payment_method = PaymentMethod.objects.create(name='Google Pay')
        
        # Initially True (default)
        self.assertTrue(payment_method.is_active)
        
        # Deactivate
        payment_method.is_active = False
        payment_method.save()
        payment_method.refresh_from_db()
        self.assertFalse(payment_method.is_active)
        
        # Reactivate
        payment_method.is_active = True
        payment_method.save()
        payment_method.refresh_from_db()
        self.assertTrue(payment_method.is_active)


class PaymentMethodStringRepresentationTests(TestCase):
    """Test cases for PaymentMethod string representation."""
    
    def test_str_method_returns_name(self):
        """Test that __str__ returns the name field."""
        payment_method = PaymentMethod.objects.create(
            name='Venmo',
            description='Digital wallet payment'
        )
        
        self.assertEqual(str(payment_method), 'Venmo')
    
    def test_str_method_with_special_characters(self):
        """Test __str__ with special characters in name."""
        payment_method = PaymentMethod.objects.create(
            name='WeChat Pay (微信支付)'
        )
        
        self.assertEqual(str(payment_method), 'WeChat Pay (微信支付)')


class PaymentMethodQuerySetTests(TestCase):
    """Test cases for PaymentMethod QuerySet operations."""
    
    def setUp(self):
        """Set up test data."""
        PaymentMethod.objects.create(name='Cash', is_active=True)
        PaymentMethod.objects.create(name='Credit Card', is_active=True)
        PaymentMethod.objects.create(name='Old Method', is_active=False)
        PaymentMethod.objects.create(name='Bitcoin', is_active=True)
        PaymentMethod.objects.create(name='Deprecated', is_active=False)
    
    def test_filter_active_payment_methods(self):
        """Test filtering to get only active payment methods."""
        active_methods = PaymentMethod.objects.filter(is_active=True)
        
        self.assertEqual(active_methods.count(), 3)
        names = [method.name for method in active_methods]
        self.assertIn('Cash', names)
        self.assertIn('Credit Card', names)
        self.assertIn('Bitcoin', names)
    
    def test_filter_inactive_payment_methods(self):
        """Test filtering to get only inactive payment methods."""
        inactive_methods = PaymentMethod.objects.filter(is_active=False)
        
        self.assertEqual(inactive_methods.count(), 2)
        names = [method.name for method in inactive_methods]
        self.assertIn('Old Method', names)
        self.assertIn('Deprecated', names)
    
    def test_default_ordering_by_name(self):
        """Test that payment methods are ordered by name alphabetically."""
        all_methods = list(PaymentMethod.objects.all())
        names = [method.name for method in all_methods]
        
        # Should be in alphabetical order
        expected_order = ['Bitcoin', 'Cash', 'Credit Card', 'Deprecated', 'Old Method']
        self.assertEqual(names, expected_order)
    
    def test_get_by_name(self):
        """Test retrieving a specific payment method by name."""
        method = PaymentMethod.objects.get(name='Credit Card')
        
        self.assertEqual(method.name, 'Credit Card')
        self.assertTrue(method.is_active)
    
    def test_count_total_payment_methods(self):
        """Test counting total payment methods."""
        total = PaymentMethod.objects.count()
        
        self.assertEqual(total, 5)


class PaymentMethodMetaOptionsTests(TestCase):
    """Test cases for PaymentMethod Meta options."""
    
    def test_verbose_name(self):
        """Test that verbose_name is set correctly."""
        self.assertEqual(
            PaymentMethod._meta.verbose_name,
            "Payment Method"
        )
    
    def test_verbose_name_plural(self):
        """Test that verbose_name_plural is set correctly."""
        self.assertEqual(
            PaymentMethod._meta.verbose_name_plural,
            "Payment Methods"
        )
    
    def test_ordering(self):
        """Test that ordering is set to name field."""
        self.assertEqual(
            PaymentMethod._meta.ordering,
            ['name']
        )


class PaymentMethodBusinessLogicTests(TestCase):
    """Test cases for business logic scenarios with PaymentMethod."""
    
    def test_create_common_payment_methods(self):
        """Test creating a set of common payment methods."""
        common_methods = [
            ('Cash', 'Pay with physical currency', True),
            ('Credit Card', 'Pay with Visa, Mastercard, or Amex', True),
            ('Debit Card', 'Pay directly from your bank account', True),
            ('PayPal', 'Pay securely with your PayPal account', True),
            ('Apple Pay', 'Quick payment with Apple devices', True),
            ('Google Pay', 'Quick payment with Google wallet', True),
        ]
        
        for name, description, is_active in common_methods:
            PaymentMethod.objects.create(
                name=name,
                description=description,
                is_active=is_active
            )
        
        self.assertEqual(PaymentMethod.objects.count(), 6)
        active_count = PaymentMethod.objects.filter(is_active=True).count()
        self.assertEqual(active_count, 6)
    
    def test_deactivate_old_payment_methods(self):
        """Test deactivating outdated payment methods."""
        # Create some payment methods
        PaymentMethod.objects.create(name='Check', is_active=True)
        PaymentMethod.objects.create(name='Money Order', is_active=True)
        PaymentMethod.objects.create(name='Credit Card', is_active=True)
        
        # Deactivate old methods
        old_methods = ['Check', 'Money Order']
        PaymentMethod.objects.filter(name__in=old_methods).update(is_active=False)
        
        # Verify
        self.assertFalse(PaymentMethod.objects.get(name='Check').is_active)
        self.assertFalse(PaymentMethod.objects.get(name='Money Order').is_active)
        self.assertTrue(PaymentMethod.objects.get(name='Credit Card').is_active)
    
    def test_get_available_payment_options(self):
        """Test retrieving only available payment options for customers."""
        # Create mix of active and inactive
        PaymentMethod.objects.create(name='Cash', is_active=True)
        PaymentMethod.objects.create(name='Credit Card', is_active=True)
        PaymentMethod.objects.create(name='Bitcoin', is_active=False)
        PaymentMethod.objects.create(name='Wire Transfer', is_active=False)
        
        # Get available options (what customer should see)
        available = PaymentMethod.objects.filter(is_active=True).order_by('name')
        
        self.assertEqual(available.count(), 2)
        names = [method.name for method in available]
        self.assertEqual(names, ['Cash', 'Credit Card'])
    
    def test_update_payment_method_description(self):
        """Test updating payment method details."""
        method = PaymentMethod.objects.create(
            name='Apple Pay',
            description='Original description'
        )
        
        # Update description
        method.description = 'Pay quickly and securely using Apple Pay on your iPhone, iPad, or Mac'
        method.save()
        
        method.refresh_from_db()
        self.assertEqual(
            method.description,
            'Pay quickly and securely using Apple Pay on your iPhone, iPad, or Mac'
        )
    
    def test_bulk_create_payment_methods(self):
        """Test bulk creating multiple payment methods."""
        methods = [
            PaymentMethod(name='Visa', description='Visa credit card'),
            PaymentMethod(name='Mastercard', description='Mastercard credit card'),
            PaymentMethod(name='Amex', description='American Express card'),
        ]
        
        PaymentMethod.objects.bulk_create(methods)
        
        self.assertEqual(PaymentMethod.objects.count(), 3)


class PaymentMethodEdgeCasesTests(TestCase):
    """Test cases for edge cases and error conditions."""
    
    def test_empty_name_not_allowed(self):
        """Test that empty name is not allowed."""
        payment_method = PaymentMethod(name='')
        
        with self.assertRaises(ValidationError) as context:
            payment_method.full_clean()
        
        self.assertIn('name', context.exception.message_dict)
    
    def test_whitespace_only_name(self):
        """Test payment method with whitespace-only name."""
        payment_method = PaymentMethod.objects.create(name='   ')
        
        # Django allows it, but it's probably not good practice
        self.assertEqual(payment_method.name, '   ')
    
    def test_special_characters_in_name(self):
        """Test that special characters are allowed in name."""
        special_names = [
            'Credit/Debit Card',
            'Pay-Pal',
            'Apple Pay™',
            'E-Wallet (Online)',
        ]
        
        for name in special_names:
            method = PaymentMethod.objects.create(name=name)
            self.assertEqual(method.name, name)
    
    def test_unicode_in_name(self):
        """Test Unicode characters in name field."""
        payment_method = PaymentMethod.objects.create(
            name='支付宝 (Alipay)'
        )
        
        self.assertEqual(payment_method.name, '支付宝 (Alipay)')
    
    def test_description_with_html(self):
        """Test description field with HTML content."""
        payment_method = PaymentMethod.objects.create(
            name='Online',
            description='<p>Pay online with <strong>credit card</strong></p>'
        )
        
        # TextField stores as-is (HTML not rendered)
        self.assertIn('<p>', payment_method.description)
        self.assertIn('<strong>', payment_method.description)
