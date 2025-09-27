"""
Django Integration Examples for Session Manager

This module demonstrates how to integrate the custom session manager
with Django views and middleware for ride-sharing or food delivery apps.
Shows real-world usage patterns for driver/rider session management.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
import uuid
import logging

from restaurant_management.utils.session_manager import (
    SessionManager, 
    SlidingSessionManager,
    PersistentSessionManager
)

logger = logging.getLogger(__name__)

# Global session managers for different user types
# WARNING: These are for DEMONSTRATION PURPOSES ONLY in development environments.
# In production Django applications with concurrent access, consider using:
# - Thread-local storage: threading.local()
# - Redis-backed sessions: django-redis
# - Database-backed sessions: django.contrib.sessions
# - Proper locking mechanisms for thread safety
# The current implementation is NOT thread-safe for concurrent requests.
driver_session_manager = SlidingSessionManager(expiry_seconds=1800)  # 30 minutes with sliding
rider_session_manager = SessionManager(expiry_seconds=3600)  # 1 hour fixed
delivery_session_manager = PersistentSessionManager(expiry_seconds=2700)  # 45 minutes persistent


# Thread-safe alternative for production use
import threading
thread_local_sessions = threading.local()

def get_thread_safe_session_manager(user_type='rider'):
    """
    Thread-safe session manager factory using thread-local storage.
    
    This approach ensures each thread has its own session manager instance,
    preventing race conditions in concurrent Django applications.
    
    Args:
        user_type (str): Type of session manager to create
        
    Returns:
        SessionManager: Thread-local session manager instance
    """
    if not hasattr(thread_local_sessions, user_type):
        if user_type == 'driver':
            setattr(thread_local_sessions, user_type, SlidingSessionManager(expiry_seconds=1800))
        elif user_type == 'delivery':
            setattr(thread_local_sessions, user_type, PersistentSessionManager(expiry_seconds=2700))
        else:  # default to rider
            setattr(thread_local_sessions, user_type, SessionManager(expiry_seconds=3600))
    
    return getattr(thread_local_sessions, user_type)


class CustomSessionMiddleware:
    """
    Custom middleware to validate sessions for ride-sharing/delivery platform.
    
    This middleware checks for custom session tokens in requests and validates
    them using our SessionManager. Perfect for stateless microservices.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check for custom session token in headers
        session_token = request.META.get('HTTP_X_SESSION_TOKEN')
        user_type = request.META.get('HTTP_X_USER_TYPE', 'rider')
        
        if session_token:
            # Validate session based on user type
            if user_type == 'driver':
                is_valid = driver_session_manager.is_session_active(session_token)
            elif user_type == 'delivery':
                is_valid = delivery_session_manager.is_session_active(session_token)
            else:  # rider
                is_valid = rider_session_manager.is_session_active(session_token)
            
            # Add session info to request
            request.custom_session_valid = is_valid
            request.custom_session_token = session_token
            request.user_type = user_type
        else:
            request.custom_session_valid = False
            request.custom_session_token = None
            request.user_type = None
        
        response = self.get_response(request)
        return response


def require_custom_session(user_type='rider'):
    """
    Decorator to require a valid custom session for a view.
    
    Args:
        user_type (str): Type of user session to validate ('driver', 'rider', 'delivery')
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if not getattr(request, 'custom_session_valid', False):
                return JsonResponse({
                    'error': 'Invalid or expired session',
                    'code': 'SESSION_INVALID'
                }, status=401)
            
            if getattr(request, 'user_type') != user_type:
                return JsonResponse({
                    'error': f'Invalid user type. Expected {user_type}',
                    'code': 'USER_TYPE_MISMATCH'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


@method_decorator(csrf_exempt, name='dispatch')
class DriverLoginView(View):
    """
    API endpoint for driver login in ride-sharing platform.
    Creates a sliding session that refreshes on each API call.
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            driver_id = data.get('driver_id')
            password = data.get('password')
            
            if not driver_id or not password:
                return JsonResponse({
                    'error': 'driver_id and password required',
                    'success': False
                }, status=400)
            
            # Simulate driver authentication (replace with real auth)
            if self._authenticate_driver(driver_id, password):
                # Generate unique session token
                session_token = f"driver_{driver_id}_{uuid.uuid4().hex[:16]}"
                
                # Create sliding session for active drivers
                driver_session_manager.create_session(session_token)
                
                logger.info(f"Driver {driver_id} logged in with session {session_token}")
                
                return JsonResponse({
                    'success': True,
                    'session_token': session_token,
                    'user_type': 'driver',
                    'expires_in': driver_session_manager.expiry_seconds,
                    'session_type': 'sliding',
                    'message': 'Driver logged in successfully'
                })
            else:
                return JsonResponse({
                    'error': 'Invalid credentials',
                    'success': False
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"Driver login error: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'success': False
            }, status=500)
    
    def _authenticate_driver(self, driver_id, password):
        """Simulate driver authentication. Replace with real logic."""
        # In real implementation, check against database
        return len(driver_id) > 3 and len(password) > 5


@method_decorator(csrf_exempt, name='dispatch')
class RiderLoginView(View):
    """
    API endpoint for rider login in ride-sharing platform.
    Creates a fixed-duration session for riders.
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            rider_id = data.get('rider_id')
            password = data.get('password')
            
            if not rider_id or not password:
                return JsonResponse({
                    'error': 'rider_id and password required',
                    'success': False
                }, status=400)
            
            # Simulate rider authentication
            if self._authenticate_rider(rider_id, password):
                # Generate unique session token
                session_token = f"rider_{rider_id}_{uuid.uuid4().hex[:16]}"
                
                # Create fixed session for riders
                rider_session_manager.create_session(session_token)
                
                logger.info(f"Rider {rider_id} logged in with session {session_token}")
                
                return JsonResponse({
                    'success': True,
                    'session_token': session_token,
                    'user_type': 'rider',
                    'expires_in': rider_session_manager.expiry_seconds,
                    'session_type': 'fixed',
                    'message': 'Rider logged in successfully'
                })
            else:
                return JsonResponse({
                    'error': 'Invalid credentials',
                    'success': False
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"Rider login error: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'success': False
            }, status=500)
    
    def _authenticate_rider(self, rider_id, password):
        """Simulate rider authentication. Replace with real logic."""
        return len(rider_id) > 3 and len(password) > 5


@method_decorator(csrf_exempt, name='dispatch')
class DeliveryDriverLoginView(View):
    """
    API endpoint for delivery driver login in food delivery platform.
    Uses persistent sessions that survive app restarts.
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            driver_id = data.get('driver_id')
            password = data.get('password')
            
            if not driver_id or not password:
                return JsonResponse({
                    'error': 'driver_id and password required',
                    'success': False
                }, status=400)
            
            # Simulate authentication
            if self._authenticate_delivery_driver(driver_id, password):
                # Generate unique session token
                session_token = f"delivery_{driver_id}_{uuid.uuid4().hex[:16]}"
                
                # Create persistent session for delivery drivers
                delivery_session_manager.create_session(session_token)
                
                logger.info(f"Delivery driver {driver_id} logged in with session {session_token}")
                
                return JsonResponse({
                    'success': True,
                    'session_token': session_token,
                    'user_type': 'delivery',
                    'expires_in': delivery_session_manager.expiry_seconds,
                    'session_type': 'persistent',
                    'message': 'Delivery driver logged in successfully'
                })
            else:
                return JsonResponse({
                    'error': 'Invalid credentials',
                    'success': False
                }, status=401)
                
        except Exception as e:
            logger.error(f"Delivery driver login error: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'success': False
            }, status=500)
    
    def _authenticate_delivery_driver(self, driver_id, password):
        """Simulate delivery driver authentication."""
        return len(driver_id) > 3 and len(password) > 5


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    """
    Universal logout endpoint for all user types.
    """
    
    def post(self, request):
        session_token = request.META.get('HTTP_X_SESSION_TOKEN')
        user_type = request.META.get('HTTP_X_USER_TYPE', 'rider')
        
        if not session_token:
            return JsonResponse({
                'error': 'No session token provided',
                'success': False
            }, status=400)
        
        # Delete session based on user type
        if user_type == 'driver':
            result = driver_session_manager.delete_session(session_token)
        elif user_type == 'delivery':
            result = delivery_session_manager.delete_session(session_token)
        else:  # rider
            result = rider_session_manager.delete_session(session_token)
        
        if result == "Deleted":
            logger.info(f"{user_type} session {session_token[:16]}... logged out")
            return JsonResponse({
                'success': True,
                'message': f'{user_type.title()} logged out successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Session not found or already expired'
            }, status=404)


@require_custom_session('driver')
@csrf_exempt
def driver_location_update(request):
    """
    API endpoint for drivers to update their location.
    Requires valid driver session. Perfect example of sliding session usage.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if latitude is None or longitude is None:
                return JsonResponse({
                    'error': 'latitude and longitude required',
                    'success': False
                }, status=400)
            
            # Session is automatically refreshed by sliding session manager
            # when is_session_active was called in middleware
            
            # Simulate location update (replace with real logic)
            logger.info(f"Driver location updated: {latitude}, {longitude}")
            
            return JsonResponse({
                'success': True,
                'message': 'Location updated successfully',
                'session_refreshed': True
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'success': False
            }, status=400)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)


@require_custom_session('rider')
@csrf_exempt  
def request_ride(request):
    """
    API endpoint for riders to request a ride.
    Requires valid rider session.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pickup_lat = data.get('pickup_latitude')
            pickup_lng = data.get('pickup_longitude')
            destination_lat = data.get('destination_latitude')
            destination_lng = data.get('destination_longitude')
            
            if not all([pickup_lat, pickup_lng, destination_lat, destination_lng]):
                return JsonResponse({
                    'error': 'All location coordinates required',
                    'success': False
                }, status=400)
            
            # Simulate ride request processing
            ride_id = f"ride_{uuid.uuid4().hex[:12]}"
            
            logger.info(f"Ride requested: {ride_id}")
            
            return JsonResponse({
                'success': True,
                'ride_id': ride_id,
                'message': 'Ride requested successfully',
                'estimated_arrival': '5-10 minutes'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'success': False
            }, status=400)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)


@require_custom_session('delivery')
@csrf_exempt
def delivery_status_update(request):
    """
    API endpoint for delivery drivers to update order status.
    Uses persistent sessions for reliability.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            status_update = data.get('status')
            
            if not order_id or not status_update:
                return JsonResponse({
                    'error': 'order_id and status required',
                    'success': False
                }, status=400)
            
            # Simulate status update
            logger.info(f"Order {order_id} status updated to: {status_update}")
            
            return JsonResponse({
                'success': True,
                'message': f'Order status updated to {status_update}',
                'order_id': order_id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'success': False
            }, status=400)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)


class SessionStatusView(View):
    """
    API endpoint to check session status and get session information.
    Useful for debugging and monitoring.
    """
    
    def get(self, request):
        session_token = request.META.get('HTTP_X_SESSION_TOKEN')
        user_type = request.META.get('HTTP_X_USER_TYPE', 'rider')
        
        if not session_token:
            return JsonResponse({
                'error': 'No session token provided',
                'success': False
            }, status=400)
        
        # Get session info based on user type
        if user_type == 'driver':
            session_info = driver_session_manager.get_session_info(session_token)
            active_count = driver_session_manager.get_active_session_count()
        elif user_type == 'delivery':
            session_info = delivery_session_manager.get_session_info(session_token)
            active_count = delivery_session_manager.get_active_session_count()
        else:  # rider
            session_info = rider_session_manager.get_session_info(session_token)
            active_count = rider_session_manager.get_active_session_count()
        
        if session_info:
            return JsonResponse({
                'success': True,
                'session_info': session_info,
                'total_active_sessions': active_count,
                'user_type': user_type
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Session not found or expired',
                'total_active_sessions': active_count,
                'user_type': user_type
            }, status=404)


# Example Django management command for session cleanup
"""
# management/commands/cleanup_expired_sessions.py
from django.core.management.base import BaseCommand
from myapp.session_integration import (
    driver_session_manager, 
    rider_session_manager, 
    delivery_session_manager
)

class Command(BaseCommand):
    help = 'Clean up expired sessions from all session managers'
    
    def handle(self, *args, **options):
        driver_cleaned = driver_session_manager.cleanup_expired_sessions()
        rider_cleaned = rider_session_manager.cleanup_expired_sessions()
        delivery_cleaned = delivery_session_manager.cleanup_expired_sessions()
        
        total_cleaned = driver_cleaned + rider_cleaned + delivery_cleaned
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaned up {total_cleaned} expired sessions:\\n'
                f'  Drivers: {driver_cleaned}\\n'
                f'  Riders: {rider_cleaned}\\n'
                f'  Delivery: {delivery_cleaned}'
            )
        )
"""


# Example URL patterns for Django urls.py
"""
from django.urls import path
from . import session_integration

urlpatterns = [
    # Authentication endpoints
    path('api/auth/driver/login/', session_integration.DriverLoginView.as_view(), name='driver_login'),
    path('api/auth/rider/login/', session_integration.RiderLoginView.as_view(), name='rider_login'),
    path('api/auth/delivery/login/', session_integration.DeliveryDriverLoginView.as_view(), name='delivery_login'),
    path('api/auth/logout/', session_integration.LogoutView.as_view(), name='logout'),
    
    # Protected endpoints
    path('api/driver/location/', session_integration.driver_location_update, name='driver_location'),
    path('api/rider/request-ride/', session_integration.request_ride, name='request_ride'),
    path('api/delivery/status/', session_integration.delivery_status_update, name='delivery_status'),
    
    # Utility endpoints
    path('api/session/status/', session_integration.SessionStatusView.as_view(), name='session_status'),
]
"""


# Example settings.py configuration
"""
# Add custom middleware to MIDDLEWARE setting
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'myapp.session_integration.CustomSessionMiddleware',  # Add this
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]

# Session manager settings
SESSION_MANAGER_SETTINGS = {
    'DRIVER_SESSION_EXPIRY': 1800,  # 30 minutes
    'RIDER_SESSION_EXPIRY': 3600,   # 1 hour  
    'DELIVERY_SESSION_EXPIRY': 2700, # 45 minutes
    'PERSISTENT_STORAGE_FILE': 'delivery_sessions.json',
}
"""

# Example usage in other views
def example_usage():
    """
    Example of how to use the session managers in your own code.
    """
    from restaurant_management.utils.session_manager import SessionManager
    
    # Create a session manager for your specific use case
    custom_sm = SessionManager(expiry_seconds=900)  # 15 minutes
    
    # Create a session for a user
    user_id = "user123"
    custom_sm.create_session(user_id)
    
    # Check if session is active
    if custom_sm.is_session_active(user_id):
        print("User is logged in")
        
        # Get session details
        info = custom_sm.get_session_info(user_id)
        print(f"Session expires in {info['remaining_seconds']} seconds")
    
    # Log user out
    result = custom_sm.delete_session(user_id)
    print(f"Session deletion: {result}")  # "Deleted" or "Not Found"