"""
Email utilities for the restaurant management system.

This module provides reusable functions for sending various types of emails
including order confirmations, notifications, and other communications.
"""

import logging
from typing import Dict, List, Optional, Union
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from orders.models import Order, OrderItem

# Set up logging
logger = logging.getLogger(__name__)


class EmailSendingError(Exception):
    """Custom exception for email sending failures."""
    pass


def send_order_confirmation_email(
    order_id: int,
    customer_email: str,
    customer_name: Optional[str] = None,
    **kwargs
) -> Dict[str, Union[bool, str]]:
    """
    Send an order confirmation email to the customer.
    
    Args:
        order_id (int): The ID of the order to confirm
        customer_email (str): Email address to send confirmation to
        customer_name (str, optional): Customer's name for personalization
        **kwargs: Additional context variables for email template
    
    Returns:
        Dict containing:
            - success (bool): Whether email was sent successfully
            - message (str): Success message or error description
            - email_sent (bool): Whether email was actually sent
    
    Raises:
        EmailSendingError: If critical email sending fails
    """
    
    try:
        # Validate email address
        validate_email(customer_email)
        logger.info(f"Sending order confirmation email for order {order_id} to {customer_email}")
        
        # Get order details
        try:
            order = Order.objects.select_related('status', 'customer', 'user').prefetch_related(
                'order_items__menu_item'
            ).get(id=order_id)
        except Order.DoesNotExist:
            error_msg = f"Order with ID {order_id} not found"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'email_sent': False
            }
        
        # Determine customer name
        if not customer_name:
            if order.user:
                customer_name = order.user.get_full_name() or order.user.username
            elif order.customer and order.customer.name:
                customer_name = order.customer.name
            else:
                customer_name = "Valued Customer"
        
        # Prepare email context
        context = {
            'order': order,
            'customer_name': customer_name,
            'order_items': order.order_items.all(),
            'restaurant_name': 'Perpex Bistro',
            'support_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@perpexbistro.com'),
            **kwargs  # Allow additional context variables
        }
        
        # Create email subject
        subject = f'Order Confirmation #{order.id} - Perpex Bistro'
        
        # Create email body (text version)
        message = _create_order_confirmation_text(context)
        
        # Send email
        email_sent = send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[customer_email],
            fail_silently=False
        )
        
        if email_sent:
            logger.info(f"Order confirmation email successfully sent for order {order_id}")
            return {
                'success': True,
                'message': f'Order confirmation email sent successfully to {customer_email}',
                'email_sent': True
            }
        else:
            logger.warning(f"Email sending returned False for order {order_id}")
            return {
                'success': False,
                'message': 'Email sending failed - no error returned',
                'email_sent': False
            }
            
    except ValidationError as e:
        error_msg = f"Invalid email address: {customer_email}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'email_sent': False
        }
        
    except Exception as e:
        error_msg = f"Failed to send order confirmation email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Decide whether to raise or return error
        if isinstance(e, (ConnectionError, OSError)):
            # Network/connection issues - return error but don't crash
            return {
                'success': False,
                'message': f'Email service temporarily unavailable: {str(e)}',
                'email_sent': False
            }
        else:
            # Other errors - might want to raise for debugging
            return {
                'success': False,
                'message': error_msg,
                'email_sent': False
            }


def send_order_confirmation_html_email(
    order_id: int,
    customer_email: str,
    customer_name: Optional[str] = None,
    template_name: str = 'emails/order_confirmation.html',
    **kwargs
) -> Dict[str, Union[bool, str]]:
    """
    Send an HTML order confirmation email using Django templates.
    
    Args:
        order_id (int): The ID of the order to confirm
        customer_email (str): Email address to send confirmation to
        customer_name (str, optional): Customer's name for personalization
        template_name (str): Path to HTML email template
        **kwargs: Additional context variables for email template
    
    Returns:
        Dict containing success status and message
    """
    
    try:
        # Validate email address
        validate_email(customer_email)
        logger.info(f"Sending HTML order confirmation email for order {order_id}")
        
        # Get order details
        try:
            order = Order.objects.select_related('status', 'customer', 'user').prefetch_related(
                'order_items__menu_item'
            ).get(id=order_id)
        except Order.DoesNotExist:
            error_msg = f"Order with ID {order_id} not found"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'email_sent': False
            }
        
        # Determine customer name
        if not customer_name:
            if order.user:
                customer_name = order.user.get_full_name() or order.user.username
            elif order.customer and order.customer.name:
                customer_name = order.customer.name
            else:
                customer_name = "Valued Customer"
        
        # Prepare context for template
        context = {
            'order': order,
            'customer_name': customer_name,
            'order_items': order.order_items.all(),
            'restaurant_name': 'Perpex Bistro',
            'support_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@perpexbistro.com'),
            **kwargs
        }
        
        # Render HTML email
        try:
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
        except Exception as e:
            # Fall back to text email if template rendering fails
            logger.warning(f"Template rendering failed, falling back to text email: {e}")
            return send_order_confirmation_email(order_id, customer_email, customer_name, **kwargs)
        
        # Create email
        subject = f'Order Confirmation #{order.id} - Perpex Bistro'
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[customer_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email_sent = email.send(fail_silently=False)
        
        if email_sent:
            logger.info(f"HTML order confirmation email successfully sent for order {order_id}")
            return {
                'success': True,
                'message': f'Order confirmation email sent successfully to {customer_email}',
                'email_sent': True
            }
        else:
            return {
                'success': False,
                'message': 'Email sending failed',
                'email_sent': False
            }
            
    except Exception as e:
        error_msg = f"Failed to send HTML order confirmation email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'message': error_msg,
            'email_sent': False
        }


def _create_order_confirmation_text(context: Dict) -> str:
    """
    Create a text-based order confirmation email body.
    
    Args:
        context (Dict): Email context containing order and customer details
        
    Returns:
        str: Formatted email text content
    """
    order = context['order']
    customer_name = context['customer_name']
    restaurant_name = context.get('restaurant_name', 'Perpex Bistro')
    support_email = context.get('support_email', 'support@perpexbistro.com')
    
    # Calculate total
    total_amount = f"${order.total_amount:.2f}"
    
    # Build order items list
    items_text = []
    for item in context['order_items']:
        item_total = item.quantity * item.price
        items_text.append(
            f"  • {item.menu_item.name} x{item.quantity} - ${item_total:.2f}"
        )
    
    # Create email body
    email_body = f"""
Dear {customer_name},

Thank you for your order with {restaurant_name}!

ORDER CONFIRMATION
==================
Order Number: #{order.id}
Order Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}
Status: {order.status.name if order.status else 'Pending'}

ORDER DETAILS
=============
{chr(10).join(items_text)}

Total: {total_amount}

We're preparing your order and will have it ready soon. You'll receive another email when your order is ready for pickup/delivery.

If you have any questions about your order, please contact us at {support_email}.

Thank you for choosing {restaurant_name}!

Best regards,
The {restaurant_name} Team
"""
    
    return email_body.strip()


# Utility function for bulk email sending
def send_bulk_order_notifications(
    orders: List[int],
    email_type: str = 'confirmation',
    **kwargs
) -> Dict[str, Union[int, List[str]]]:
    """
    Send bulk order notifications.
    
    Args:
        orders (List[int]): List of order IDs
        email_type (str): Type of email to send ('confirmation', 'ready', etc.)
        **kwargs: Additional arguments passed to individual email functions
        
    Returns:
        Dict with success/failure counts and any error messages
    """
    
    results = {
        'total_orders': len(orders),
        'successful_emails': 0,
        'failed_emails': 0,
        'errors': []
    }
    
    for order_id in orders:
        try:
            # Get order to extract email
            order = Order.objects.select_related('user', 'customer').get(id=order_id)
            
            # Determine email address
            if order.user and order.user.email:
                email = order.user.email
            elif order.customer and order.customer.email:
                email = order.customer.email
            else:
                results['failed_emails'] += 1
                results['errors'].append(f"Order {order_id}: No email address found")
                continue
            
            # Send email based on type
            if email_type == 'confirmation':
                result = send_order_confirmation_email(order_id, email, **kwargs)
            else:
                results['failed_emails'] += 1
                results['errors'].append(f"Order {order_id}: Unknown email type '{email_type}'")
                continue
            
            if result['success']:
                results['successful_emails'] += 1
            else:
                results['failed_emails'] += 1
                results['errors'].append(f"Order {order_id}: {result['message']}")
                
        except Order.DoesNotExist:
            results['failed_emails'] += 1 
            results['errors'].append(f"Order {order_id}: Order not found")
        except Exception as e:
            results['failed_emails'] += 1
            results['errors'].append(f"Order {order_id}: {str(e)}")
    
    return results