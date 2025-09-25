"""
Example integration of email confirmation functionality into Django views.

This file demonstrates how to integrate the order confirmation email
functionality into your existing order creation and management views.
"""

from django.http import JsonResponse
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.email_utils import send_order_confirmation_email
import logging

logger = logging.getLogger(__name__)


class OrderCreateViewWithEmail(APIView):
    """
    Example of how to integrate email confirmation into order creation.
    This extends the existing CreateOrderView functionality.
    """
    
    def post(self, request, *args, **kwargs):
        # ... existing order creation logic ...
        # (This would typically create the order first)
        
        # After successful order creation, send confirmation email
        order_id = 123  # This would be the actual created order ID
        customer_email = request.data.get('customer_email')
        customer_name = request.data.get('customer_name')
        
        if customer_email:
            try:
                email_result = send_order_confirmation_email(
                    order_id=order_id,
                    customer_email=customer_email,
                    customer_name=customer_name
                )
                
                # Include email status in response
                response_data = {
                    'success': True,
                    'order_id': order_id,
                    'message': 'Order created successfully',
                    'email_confirmation': {
                        'sent': email_result['email_sent'],
                        'message': email_result['message']
                    }
                }
                
                if not email_result['success']:
                    # Log email failure but don't fail the order creation
                    logger.warning(f"Email confirmation failed for order {order_id}: {email_result['message']}")
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # Email failure shouldn't break order creation
                logger.error(f"Unexpected error sending confirmation email: {e}")
                return Response({
                    'success': True,
                    'order_id': order_id,
                    'message': 'Order created successfully',
                    'email_confirmation': {
                        'sent': False,
                        'message': 'Email confirmation failed but order was created'
                    }
                }, status=status.HTTP_201_CREATED)
        
        # If no email provided, just return success without email
        return Response({
            'success': True,
            'order_id': order_id,
            'message': 'Order created successfully',
            'email_confirmation': {
                'sent': False,
                'message': 'No email address provided'
            }
        }, status=status.HTTP_201_CREATED)


def send_confirmation_after_order_creation(order_id, user=None, customer_email=None):
    """
    Utility function to send confirmation email after order creation.
    Can be called from any view or signal handler.
    
    Args:
        order_id (int): ID of the created order
        user (User, optional): Django user if authenticated order
        customer_email (str, optional): Email for guest orders
    
    Returns:
        dict: Email sending result
    """
    
    # Determine email and name
    if user and user.email:
        email = user.email
        name = user.get_full_name() or user.username
    elif customer_email:
        email = customer_email
        name = None
    else:
        logger.warning(f"No email available for order {order_id} confirmation")
        return {
            'success': False,
            'message': 'No email address available',
            'email_sent': False
        }
    
    # Send confirmation
    try:
        result = send_order_confirmation_email(
            order_id=order_id,
            customer_email=email,
            customer_name=name
        )
        
        if result['success']:
            logger.info(f"Confirmation email sent for order {order_id}")
        else:
            logger.warning(f"Failed to send confirmation for order {order_id}: {result['message']}")
        
        return result
        
    except Exception as e:
        error_msg = f"Error sending confirmation for order {order_id}: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'email_sent': False
        }


# Example Django signal handler
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order

@receiver(post_save, sender=Order)
def send_order_confirmation_on_creation(sender, instance, created, **kwargs):
    """
    Signal handler to automatically send confirmation emails when orders are created.
    
    To use this, add it to your signals.py file and make sure signals are loaded.
    """
    
    if created:  # Only for new orders
        # Determine email with safe attribute access
        email = None
        name = None
        
        if hasattr(instance, 'user') and instance.user and hasattr(instance.user, 'email') and instance.user.email:
            email = instance.user.email
            name = instance.user.get_full_name() or instance.user.username
        elif hasattr(instance, 'customer') and instance.customer and hasattr(instance.customer, 'email') and instance.customer.email:
            email = instance.customer.email
            if hasattr(instance.customer, 'name'):
                name = instance.customer.name
        
        if not email:
            # No email available, skip confirmation
            return
        
        # Send confirmation email asynchronously (if using Celery) or synchronously
        try:
            result = send_order_confirmation_email(
                order_id=instance.id,
                customer_email=email,
                customer_name=name
            )
            
            if not result['success']:
                logger.warning(f"Auto-confirmation failed for order {instance.id}: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error in auto-confirmation for order {instance.id}: {e}")


# Example management command usage
"""
You can also create a management command to send confirmation emails in bulk:

# management/commands/send_confirmation_emails.py
from django.core.management.base import BaseCommand
from orders.email_utils import send_bulk_order_notifications
from orders.models import Order

class Command(BaseCommand):
    help = 'Send confirmation emails for orders missing confirmations'
    
    def add_arguments(self, parser):
        parser.add_argument('--order-ids', nargs='+', type=int, help='Specific order IDs')
        parser.add_argument('--all-recent', action='store_true', help='All recent orders')
    
    def handle(self, *args, **options):
        if options['order_ids']:
            order_ids = options['order_ids']
        elif options['all_recent']:
            # Get recent orders without confirmations
            order_ids = list(Order.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=1)
            ).values_list('id', flat=True))
        else:
            self.stdout.write(self.style.ERROR('Please specify --order-ids or --all-recent'))
            return
        
        results = send_bulk_order_notifications(order_ids, email_type='confirmation')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Sent {results["successful_emails"]} emails, '
                f'{results["failed_emails"]} failed'
            )
        )
        
        if results['errors']:
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f'Error: {error}'))
"""