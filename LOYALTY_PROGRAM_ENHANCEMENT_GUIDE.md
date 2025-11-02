# LoyaltyProgram Model Enhancement Guide

## Overview

This guide documents the enhancements made to the `LoyaltyProgram` model, adding support for customer earning rates and program status management.

**Enhancement Date:** November 6, 2024  
**Migration:** `0024_loyaltyprogram_is_active_and_more`  
**Tests:** 22 comprehensive tests  
**Status:** ✅ Complete - All tests passing

---

## New Fields Added

### 1. `points_per_dollar_spent`

**Type:** `DecimalField(max_digits=5, decimal_places=2)`  
**Default:** `1.0`  
**Validator:** `MinValueValidator(0)`

Defines how many loyalty points a customer earns for each dollar spent.

**Purpose:**
- Enables tiered earning systems where higher tiers earn points faster
- Allows flexible loyalty program configurations
- Supports promotional earning rate adjustments

**Example Values:**
- `1.0` - Standard earning rate (1 point per dollar)
- `1.5` - Enhanced earning rate (Gold tier members)
- `2.0` - Premium earning rate (Platinum tier members)
- `0.5` - Reduced earning rate (promotional tiers)
- `0.0` - Non-earning tier (trial programs)

**Constraints:**
- Must be non-negative (≥ 0)
- Maximum value: 999.99
- Precision: 2 decimal places

**Example Usage:**
```python
# Bronze tier: standard earning rate
bronze = LoyaltyProgram.objects.create(
    name='Bronze Member',
    points_required=0,
    points_per_dollar_spent=Decimal('1.0'),
    discount_percentage=Decimal('5.00'),
    description='Entry level loyalty tier'
)

# Calculate points earned on a $150 purchase
purchase_amount = Decimal('150.00')
points_earned = purchase_amount * bronze.points_per_dollar_spent
# Result: 150 points
```

---

### 2. `is_active`

**Type:** `BooleanField`  
**Default:** `True`

Flag to indicate if the loyalty program is currently active.

**Purpose:**
- Enable/disable programs without deleting them
- Preserve historical program data
- Support seasonal or time-limited programs
- Allow easy program management in admin interface

**States:**
- `True` - Program is active and available to customers
- `False` - Program is inactive (archived or disabled)

**Example Usage:**
```python
# Create an active program
gold_tier = LoyaltyProgram.objects.create(
    name='Gold Member',
    points_required=1000,
    points_per_dollar_spent=Decimal('1.5'),
    discount_percentage=Decimal('15.00'),
    is_active=True
)

# Deactivate old programs
old_programs = LoyaltyProgram.objects.filter(name__contains='2023')
old_programs.update(is_active=False)

# Get only active programs
active_programs = LoyaltyProgram.objects.filter(is_active=True)
```

---

## Complete Model Structure

The enhanced `LoyaltyProgram` model now includes:

### Fields

| Field Name | Type | Default | Validators | Description |
|------------|------|---------|------------|-------------|
| `name` | CharField(200) | - | unique=True | Name of the loyalty program tier |
| `points_required` | IntegerField | - | MinValueValidator(0) | Points needed to reach this tier |
| `points_per_dollar_spent` | DecimalField(5,2) | 1.0 | MinValueValidator(0) | **NEW:** Earning rate per dollar |
| `discount_percentage` | DecimalField(5,2) | - | MinValueValidator(0), MaxValueValidator(100) | Discount benefit for this tier |
| `description` | TextField | - | - | Description of the loyalty program |
| `is_active` | BooleanField | True | - | **NEW:** Whether program is active |
| `created_at` | DateTimeField | auto_now_add | - | Timestamp of creation |
| `updated_at` | DateTimeField | auto_now | - | Timestamp of last update |

### Meta Options
- **Ordering:** `['points_required']` (ascending)
- **Verbose Name:** "Loyalty Program"
- **Verbose Name Plural:** "Loyalty Programs"

### String Representation
```python
def __str__(self):
    return f"{self.name} ({self.points_required} points - {self.discount_percentage}% discount)"
```

---

## Example Loyalty Program Configurations

### Standard Three-Tier System

```python
# Bronze Tier - Entry Level
bronze = LoyaltyProgram.objects.create(
    name='Bronze Member',
    points_required=0,
    points_per_dollar_spent=Decimal('1.0'),
    discount_percentage=Decimal('5.00'),
    description='Welcome tier with standard earning rate and 5% discount',
    is_active=True
)

# Silver Tier - Mid-Level
silver = LoyaltyProgram.objects.create(
    name='Silver Member',
    points_required=500,
    points_per_dollar_spent=Decimal('1.25'),
    discount_percentage=Decimal('10.00'),
    description='Mid-tier with 25% bonus earning rate and 10% discount',
    is_active=True
)

# Gold Tier - Premium
gold = LoyaltyProgram.objects.create(
    name='Gold Member',
    points_required=1000,
    points_per_dollar_spent=Decimal('1.5'),
    discount_percentage=Decimal('15.00'),
    description='Premium tier with 50% bonus earning rate and 15% discount',
    is_active=True
)
```

### Calculate Customer Points Earned

```python
def calculate_points_for_purchase(customer_tier, purchase_amount):
    """
    Calculate loyalty points earned for a purchase.
    
    Args:
        customer_tier: LoyaltyProgram instance
        purchase_amount: Decimal amount of purchase
        
    Returns:
        Decimal: Points earned
    """
    if not customer_tier.is_active:
        return Decimal('0.00')
    
    points = purchase_amount * customer_tier.points_per_dollar_spent
    return points.quantize(Decimal('0.01'))

# Example usage
customer = User.objects.get(username='john_doe')
current_tier = LoyaltyProgram.objects.get(name='Silver Member')
purchase = Decimal('75.50')

points_earned = calculate_points_for_purchase(current_tier, purchase)
# Result: 94.38 points (75.50 * 1.25)
```

---

## Admin Interface Updates

The Django admin interface has been enhanced to display and manage the new fields:

### List Display
- `name` - Program name
- `points_required` - Points needed for tier
- `points_per_dollar_spent` - **NEW:** Earning rate
- `discount_percentage` - Discount benefit
- `is_active` - **NEW:** Active status
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### List Filters
- `is_active` - **NEW:** Filter by active/inactive status
- `created_at` - Filter by creation date
- `updated_at` - Filter by update date

### Fieldsets

**Basic Information:**
- `name` - Program name
- `description` - Program description
- `is_active` - **NEW:** Active status toggle

**Requirements & Benefits:**
- `points_required` - Tier threshold
- `points_per_dollar_spent` - **NEW:** Earning rate
- `discount_percentage` - Tier discount

*Help text:* "Points required defines tier threshold, points per dollar defines earning rate, discount percentage defines tier benefit"

**Timestamps:**
- `created_at` (read-only)
- `updated_at` (read-only)

---

## Testing Coverage

### Test Suite: `test_loyalty_program_enhancements.py`

**Total Tests:** 22  
**Status:** ✅ All passing

#### Test Classes

1. **LoyaltyProgramPointsPerDollarSpentTests** (8 tests)
   - `test_default_points_per_dollar_spent` - Verifies 1.0 default
   - `test_custom_points_per_dollar_spent` - Tests custom values
   - `test_decimal_precision_points_per_dollar` - Validates decimal storage
   - `test_zero_points_per_dollar_allowed` - Confirms zero is valid
   - `test_negative_points_per_dollar_rejected` - Ensures negative values rejected
   - `test_high_points_per_dollar_value` - Tests high earning rates
   - `test_max_digits_and_decimal_places` - Validates field constraints
   - `test_points_calculation_scenario` - Real-world calculation example

2. **LoyaltyProgramIsActiveTests** (5 tests)
   - `test_default_is_active_true` - Verifies True default
   - `test_set_is_active_false` - Tests deactivation
   - `test_toggle_is_active` - Tests status toggling
   - `test_filter_active_programs` - Tests QuerySet filtering
   - `test_is_active_boolean_field_type` - Validates field type

3. **LoyaltyProgramCombinedFieldsTests** (6 tests)
   - `test_complete_program_with_all_fields` - Full model validation
   - `test_inactive_program_still_has_earning_rate` - Data preservation
   - `test_different_tiers_different_earning_rates` - Multi-tier setup
   - `test_updated_at_changes_on_field_modification` - Timestamp behavior
   - `test_str_representation_unchanged` - String representation
   - `test_ordering_still_by_points_required` - Default ordering

4. **LoyaltyProgramBackwardsCompatibilityTests** (3 tests)
   - `test_existing_tests_still_pass` - Unique constraints
   - `test_validators_still_work` - Existing validators
   - `test_discount_percentage_validators_still_work` - Percentage validators

### Running Tests

```bash
# Run all loyalty program enhancement tests
python manage.py test orders.tests.test_loyalty_program_enhancements -v 2

# Run specific test class
python manage.py test orders.tests.test_loyalty_program_enhancements.LoyaltyProgramPointsPerDollarSpentTests

# Run specific test
python manage.py test orders.tests.test_loyalty_program_enhancements.LoyaltyProgramPointsPerDollarSpentTests.test_points_calculation_scenario
```

---

## Migration Details

### Migration: `0024_loyaltyprogram_is_active_and_more.py`

**Operations:**
1. Add `is_active` field (BooleanField, default=True)
2. Add `points_per_dollar_spent` field (DecimalField, default=1.0)

**Safe to Apply:** ✅ Yes
- Both fields have safe defaults
- No data loss
- Backwards compatible
- All existing records will receive default values

**Apply Migration:**
```bash
python manage.py migrate orders 0024
```

**Rollback (if needed):**
```bash
python manage.py migrate orders 0023
```

---

## API Considerations

If you have REST API endpoints for LoyaltyProgram, consider:

### Serializer Updates

```python
class LoyaltyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyProgram
        fields = [
            'id',
            'name',
            'points_required',
            'points_per_dollar_spent',  # NEW
            'discount_percentage',
            'description',
            'is_active',  # NEW
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
```

### Filtering Active Programs

```python
# In your viewset
class LoyaltyProgramViewSet(viewsets.ModelViewSet):
    serializer_class = LoyaltyProgramSerializer
    
    def get_queryset(self):
        """
        Optionally filter to show only active programs.
        Use ?active=true to filter.
        """
        queryset = LoyaltyProgram.objects.all()
        
        # Filter by active status
        active = self.request.query_params.get('active')
        if active is not None:
            is_active = active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
```

---

## Business Logic Examples

### Customer Tier Progression

```python
def check_tier_upgrade(user_profile, current_points):
    """
    Check if customer qualifies for a higher tier.
    
    Args:
        user_profile: UserProfile instance
        current_points: Customer's current loyalty points
        
    Returns:
        LoyaltyProgram or None: New tier if upgrade available
    """
    current_tier = user_profile.loyalty_tier
    
    # Get all active tiers higher than current
    higher_tiers = LoyaltyProgram.objects.filter(
        is_active=True,
        points_required__gt=current_tier.points_required,
        points_required__lte=current_points
    ).order_by('points_required')
    
    # Return highest qualifying tier
    return higher_tiers.last()
```

### Seasonal Earning Rate Boost

```python
def apply_seasonal_boost(start_date, end_date, multiplier=Decimal('1.5')):
    """
    Temporarily boost earning rates for all active programs.
    
    Args:
        start_date: When boost starts
        end_date: When boost ends
        multiplier: Factor to multiply earning rates by
    """
    from django.utils import timezone
    
    if start_date <= timezone.now().date() <= end_date:
        # Apply boost
        active_programs = LoyaltyProgram.objects.filter(is_active=True)
        for program in active_programs:
            original_rate = program.points_per_dollar_spent
            program.points_per_dollar_spent = original_rate * multiplier
            program.description += f" [SEASONAL BOOST: {multiplier}x points until {end_date}]"
            program.save()
```

---

## Best Practices

### 1. Always Check Active Status

```python
# Good ✅
active_programs = LoyaltyProgram.objects.filter(is_active=True)
customer_tier = active_programs.get(name='Gold Member')

# Bad ❌
customer_tier = LoyaltyProgram.objects.get(name='Gold Member')
# Might get inactive program
```

### 2. Use Decimal for Point Calculations

```python
# Good ✅
points = purchase_amount * tier.points_per_dollar_spent
points = points.quantize(Decimal('0.01'))

# Bad ❌
points = float(purchase_amount) * float(tier.points_per_dollar_spent)
# Floating point precision issues
```

### 3. Archive Instead of Delete

```python
# Good ✅
old_tier.is_active = False
old_tier.save()

# Bad ❌
old_tier.delete()
# Loses historical data
```

### 4. Validate Earning Rates

```python
# Good ✅
program.full_clean()  # Validates all fields
program.save()

# Bad ❌
program.save()  # Skips validation
```

---

## Troubleshooting

### Issue: Negative points_per_dollar_spent

**Error:** `ValidationError: Ensure this value is greater than or equal to 0.`

**Solution:**
```python
# Use positive values
program.points_per_dollar_spent = Decimal('1.5')  # ✅
program.points_per_dollar_spent = Decimal('-1.5')  # ❌
```

### Issue: Inactive programs appearing in customer view

**Solution:**
```python
# Always filter by is_active
available_tiers = LoyaltyProgram.objects.filter(is_active=True)
```

### Issue: Decimal precision errors

**Solution:**
```python
from decimal import Decimal

# Always use Decimal, not float
points_per_dollar = Decimal('1.25')  # ✅
points_per_dollar = 1.25  # ❌ (float)
```

---

## Related Files

- **Model:** `orders/models.py` (lines 144-181)
- **Admin:** `orders/admin.py` (lines 112-170)
- **Tests:** `orders/tests/test_loyalty_program_enhancements.py`
- **Migration:** `orders/migrations/0024_loyaltyprogram_is_active_and_more.py`

---

## Future Enhancements

Potential additions to consider:

1. **Time-Limited Programs**
   - `valid_from` DateField
   - `valid_until` DateField
   - Auto-activate/deactivate based on dates

2. **Maximum Discount Cap**
   - `max_discount_amount` DecimalField
   - Cap total discount per transaction

3. **Minimum Spend Requirements**
   - `min_purchase_amount` DecimalField
   - Require minimum spend for tier benefits

4. **Points Expiration**
   - `points_expiry_days` IntegerField
   - Automatic point expiration

5. **Referral Bonuses**
   - `referral_bonus_points` IntegerField
   - Bonus points for referring friends

---

## Changelog

### Version 2.0 - November 6, 2024
- ✅ Added `points_per_dollar_spent` field (earning rate)
- ✅ Added `is_active` field (program status)
- ✅ Updated admin interface
- ✅ Added 22 comprehensive tests
- ✅ Created migration 0024

### Version 1.0 - November 4, 2024
- Initial LoyaltyProgram model
- Fields: name, points_required, discount_percentage, description
- Validators for positive points and 0-100% discount

---

## Support

For questions or issues related to LoyaltyProgram enhancements:
- Check test examples in `test_loyalty_program_enhancements.py`
- Review admin interface for field descriptions
- Consult this guide for best practices

---

**Document Version:** 1.0  
**Last Updated:** November 6, 2024  
**Author:** Development Team  
**Status:** Production Ready ✅
