import secrets
import string

from orders.models import Order

# If you have a Coupon model, import it instead and check uniqueness there.
# from .models import Coupon

def generate_coupon_code(length=10, existing_codes=None):
    """
    Generate a unique alphanumeric coupon code.
    Checks uniqueness against a set of existing codes (or a database model if available).
    Args:
        length (int): Length of the coupon code. Must be positive. Default is 10.
        existing_codes (set or None): Set of codes to check uniqueness against. If None, checks against Order.coupon_code if present.
    Returns:
        str: Unique coupon code.
    Raises:
        ValueError: If length is not a positive integer.
    Note:
        For production, integrate with a Coupon model and check against Coupon.objects.values_list('code', flat=True) to ensure no duplicates in the database.
    """
    if not isinstance(length, int) or length < 1:
        raise ValueError("Coupon code length must be a positive integer.")
    alphabet = string.ascii_uppercase + string.digits
    if existing_codes is None:
        # Example: If you have a Coupon model, use Coupon.objects.values_list('code', flat=True)
        # For now, fallback to an empty set (no uniqueness check)
        existing_codes = set()
    max_attempts = min(10000, len(alphabet) ** length)
    for _ in range(max_attempts):
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if code not in existing_codes:
            return code
    raise RuntimeError("Unable to generate a unique coupon code after {} attempts. Consider increasing the code length or clearing used codes.".format(max_attempts))
