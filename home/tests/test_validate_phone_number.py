"""
Test cases for the validate_phone_number utility function.

This test module provides comprehensive coverage for phone number validation,
including valid formats, invalid formats, edge cases, and various international
phone number patterns.
"""

from django.test import TestCase
from home.utils import validate_phone_number


class ValidatePhoneNumberTests(TestCase):
    """Test cases for basic valid phone number formats."""
    
    def test_basic_10_digit_number(self):
        """Test that a basic 10-digit number is valid."""
        self.assertTrue(validate_phone_number("5551234567"))
    
    def test_number_with_hyphens(self):
        """Test phone number with hyphens (555-123-4567)."""
        self.assertTrue(validate_phone_number("555-123-4567"))
    
    def test_number_with_spaces(self):
        """Test phone number with spaces (555 123 4567)."""
        self.assertTrue(validate_phone_number("555 123 4567"))
    
    def test_number_with_dots(self):
        """Test phone number with dots (555.123.4567)."""
        self.assertTrue(validate_phone_number("555.123.4567"))
    
    def test_number_with_parentheses(self):
        """Test phone number with parentheses around area code (555) 123-4567."""
        self.assertTrue(validate_phone_number("(555) 123-4567"))
    
    def test_number_with_parentheses_no_space(self):
        """Test phone number with parentheses without space (555)123-4567."""
        self.assertTrue(validate_phone_number("(555)123-4567"))
    
    def test_number_with_mixed_separators(self):
        """Test phone number with mixed separators (555) 123.4567."""
        self.assertTrue(validate_phone_number("(555) 123.4567"))
    
    def test_number_with_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped and number is valid."""
        self.assertTrue(validate_phone_number("  555-123-4567  "))
        self.assertTrue(validate_phone_number("\t(555) 123-4567\n"))


class ValidatePhoneNumberCountryCodeTests(TestCase):
    """Test cases for phone numbers with country codes."""
    
    def test_us_country_code_with_hyphen(self):
        """Test US phone number with +1 country code and hyphens."""
        self.assertTrue(validate_phone_number("+1-555-123-4567"))
    
    def test_us_country_code_with_space(self):
        """Test US phone number with +1 country code and spaces."""
        self.assertTrue(validate_phone_number("+1 555 123 4567"))
    
    def test_us_country_code_no_separator(self):
        """Test US phone number with +1 country code without separators."""
        self.assertTrue(validate_phone_number("+15551234567"))
    
    def test_us_country_code_with_parentheses(self):
        """Test US phone number with +1 and parentheses."""
        self.assertTrue(validate_phone_number("+1 (555) 123-4567"))
    
    def test_uk_country_code(self):
        """Test UK phone number with +44 country code."""
        self.assertTrue(validate_phone_number("+44 20 7123 4567"))
    
    def test_france_country_code(self):
        """Test French phone number with +33 country code."""
        self.assertTrue(validate_phone_number("+33 1 42 86 82 00"))
    
    def test_germany_country_code(self):
        """Test German phone number with +49 country code."""
        self.assertTrue(validate_phone_number("+49 30 12345678"))
    
    def test_australia_country_code(self):
        """Test Australian phone number with +61 country code."""
        self.assertTrue(validate_phone_number("+61 2 1234 5678"))


class ValidatePhoneNumberInvalidFormatTests(TestCase):
    """Test cases for invalid phone number formats."""
    
    def test_empty_string(self):
        """Test that empty string returns False."""
        self.assertFalse(validate_phone_number(""))
    
    def test_whitespace_only(self):
        """Test that whitespace-only string returns False."""
        self.assertFalse(validate_phone_number("   "))
        self.assertFalse(validate_phone_number("\t\n"))
    
    def test_none_input(self):
        """Test that None input returns False."""
        self.assertFalse(validate_phone_number(None))
    
    def test_too_short(self):
        """Test that numbers with too few digits return False."""
        self.assertFalse(validate_phone_number("123"))
        self.assertFalse(validate_phone_number("555-123"))
        self.assertFalse(validate_phone_number("12345678"))  # Only 8 digits
    
    def test_too_long(self):
        """Test that numbers with too many digits return False."""
        self.assertFalse(validate_phone_number("12345678901234567"))  # 17 digits
        self.assertFalse(validate_phone_number("+1-555-123-4567-8901"))  # Extra digits
    
    def test_contains_letters(self):
        """Test that numbers containing letters return False."""
        self.assertFalse(validate_phone_number("555-ABC-4567"))
        self.assertFalse(validate_phone_number("abcd1234567"))
        self.assertFalse(validate_phone_number("555-123-HELP"))
    
    def test_special_characters(self):
        """Test that numbers with invalid special characters return False."""
        self.assertFalse(validate_phone_number("555@123#4567"))
        self.assertFalse(validate_phone_number("555*123*4567"))
        self.assertFalse(validate_phone_number("555_123_4567"))
    
    def test_only_separators(self):
        """Test that only separators without digits return False."""
        self.assertFalse(validate_phone_number("---"))
        self.assertFalse(validate_phone_number("()"))
        self.assertFalse(validate_phone_number(". . ."))


class ValidatePhoneNumberEdgeCaseTests(TestCase):
    """Test cases for edge cases and boundary conditions."""
    
    def test_exactly_10_digits(self):
        """Test that exactly 10 digits is valid."""
        self.assertTrue(validate_phone_number("1234567890"))
    
    def test_exactly_11_digits(self):
        """Test that exactly 11 digits is valid."""
        self.assertTrue(validate_phone_number("12345678901"))
    
    def test_exactly_12_digits(self):
        """Test that exactly 12 digits is valid."""
        self.assertTrue(validate_phone_number("123456789012"))
    
    def test_9_digits(self):
        """Test that 9 digits is invalid (too short)."""
        self.assertFalse(validate_phone_number("123456789"))
    
    def test_16_digits(self):
        """Test that 16 digits is invalid (too long)."""
        self.assertFalse(validate_phone_number("1234567890123456"))
    
    def test_all_zeros(self):
        """Test that a number with all zeros is valid (format-wise)."""
        self.assertTrue(validate_phone_number("000-000-0000"))
    
    def test_all_nines(self):
        """Test that a number with all nines is valid (format-wise)."""
        self.assertTrue(validate_phone_number("999-999-9999"))
    
    def test_multiple_plus_signs(self):
        """Test that multiple plus signs are invalid."""
        self.assertFalse(validate_phone_number("++1-555-123-4567"))
        self.assertFalse(validate_phone_number("+1-+555-123-4567"))
    
    def test_plus_in_middle(self):
        """Test that plus sign in middle is invalid."""
        self.assertFalse(validate_phone_number("555+123-4567"))


class ValidatePhoneNumberInputTypeTests(TestCase):
    """Test cases for different input types."""
    
    def test_integer_input(self):
        """Test that integer input returns False (not a string)."""
        self.assertFalse(validate_phone_number(5551234567))
    
    def test_float_input(self):
        """Test that float input returns False (not a string)."""
        self.assertFalse(validate_phone_number(555.1234567))
    
    def test_list_input(self):
        """Test that list input returns False (not a string)."""
        self.assertFalse(validate_phone_number(["555", "123", "4567"]))
    
    def test_dict_input(self):
        """Test that dictionary input returns False (not a string)."""
        self.assertFalse(validate_phone_number({"phone": "555-123-4567"}))
    
    def test_boolean_input(self):
        """Test that boolean input returns False (not a string)."""
        self.assertFalse(validate_phone_number(True))
        self.assertFalse(validate_phone_number(False))


class ValidatePhoneNumberRealWorldTests(TestCase):
    """Test cases for real-world phone number examples."""
    
    def test_common_us_formats(self):
        """Test common US phone number formats that users might enter."""
        valid_formats = [
            "(212) 555-1234",
            "212-555-1234",
            "212.555.1234",
            "212 555 1234",
            "2125551234",
            "+1 212 555 1234",
            "+1-212-555-1234",
            "+1.212.555.1234",
        ]
        for phone in valid_formats:
            with self.subTest(phone=phone):
                self.assertTrue(validate_phone_number(phone), f"Failed for: {phone}")
    
    def test_international_formats(self):
        """Test various international phone number formats."""
        valid_formats = [
            "+44 20 7946 0958",      # UK London
            "+33 1 42 86 82 00",     # France Paris
            "+49 30 12345678",       # Germany Berlin
            "+61 2 1234 5678",       # Australia Sydney
            "+81 3 1234 5678",       # Japan Tokyo
        ]
        for phone in valid_formats:
            with self.subTest(phone=phone):
                self.assertTrue(validate_phone_number(phone), f"Failed for: {phone}")
    
    def test_invalid_common_mistakes(self):
        """Test common invalid formats users might enter."""
        invalid_formats = [
            "123-45-6789",           # Too few digits
            "555-CALL-NOW",          # Contains letters
            "call 555-1234",         # Contains word
            "(555) 123-456",         # Missing last digit
            "555-1234",              # Only 7 digits
            "1-800-FLOWERS",         # Vanity number with letters
            "",                      # Empty
            "N/A",                   # Placeholder text
            "TBD",                   # To be determined
        ]
        for phone in invalid_formats:
            with self.subTest(phone=phone):
                self.assertFalse(validate_phone_number(phone), f"Should fail for: {phone}")
