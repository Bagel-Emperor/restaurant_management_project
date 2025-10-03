# Ride Booking System Documentation

## Overview
Complete ride-sharing booking system enabling riders to request rides and drivers to accept them in real-time. Built with Django REST Framework and JWT authentication.

## Architecture

### Models

#### Ride Model (`orders/models.py`)
```python
class Ride:
    # Relationships
    rider: ForeignKey(Rider)         # Who requested the ride
    driver: ForeignKey(Driver)       # Who accepted (null until accepted)
    
    # Pickup Location
    pickup_address: CharField(500)
    pickup_lat: DecimalField(9, 6)
    pickup_lng: DecimalField(9, 6)
    
    # Dropoff Location
    dropoff_address: CharField(500)
    drop_lat: DecimalField(9, 6)
    drop_lng: DecimalField(9, 6)
    
    # Status & Timestamps
    status: CharField(choices=[REQUESTED, ONGOING, COMPLETED, CANCELLED])
    requested_at: DateTimeField(auto_now_add=True)
    updated_at: DateTimeField(auto_now=True)
    accepted_at: DateTimeField(null=True)
    completed_at: DateTimeField(null=True)
    
    # Future fare fields
    estimated_fare: DecimalField(10, 2)
    final_fare: DecimalField(10, 2)
```

**Status Flow:**
```
REQUESTED → ONGOING → COMPLETED
         → CANCELLED (from any state)
```

**Key Methods:**
- `accept_ride(driver)` - Assign driver and move to ONGOING
- `complete_ride(final_fare=None)` - Mark as COMPLETED
- `cancel_ride()` - Cancel from any status except COMPLETED
- `clean()` - Validate coordinates and pickup/dropoff difference

## API Endpoints

### 1. Request Ride (Rider)
**Endpoint:** `POST /PerpexBistro/orders/ride/request/`

**Authentication:** JWT (Rider profile required)

**Request Body:**
```json
{
  "pickup_address": "Koramangala, Bangalore",
  "dropoff_address": "MG Road, Bangalore",
  "pickup_lat": 12.9352,
  "pickup_lng": 77.6147,
  "drop_lat": 12.9763,
  "drop_lng": 77.6033
}
```

**Success Response (201 CREATED):**
```json
{
  "success": true,
  "message": "Ride requested successfully",
  "ride": {
    "id": 1,
    "rider": 5,
    "rider_name": "john_rider",
    "rider_phone": "+1234567890",
    "driver": null,
    "driver_name": null,
    "driver_phone": null,
    "driver_vehicle": null,
    "driver_license": null,
    "pickup_address": "Koramangala, Bangalore",
    "pickup_lat": "12.935200",
    "pickup_lng": "77.614700",
    "dropoff_address": "MG Road, Bangalore",
    "drop_lat": "12.976300",
    "drop_lng": "77.603300",
    "status": "REQUESTED",
    "status_display": "Requested",
    "requested_at": "2025-10-03T21:13:28.881196Z",
    "updated_at": "2025-10-03T21:13:28.881213Z",
    "accepted_at": null,
    "completed_at": null,
    "estimated_fare": null,
    "final_fare": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - No JWT token
- `403 Forbidden` - User doesn't have rider profile
- `400 Bad Request` - Invalid coordinates or validation errors

### 2. View Available Rides (Driver)
**Endpoint:** `GET /PerpexBistro/orders/ride/available/`

**Authentication:** JWT (Driver profile required)

**Success Response (200 OK):**
```json
{
  "success": true,
  "count": 2,
  "rides": [
    {
      "id": 1,
      "rider": 5,
      "rider_name": "john_rider",
      "rider_phone": "+1234567890",
      "driver": null,
      "driver_name": null,
      "driver_phone": null,
      "driver_vehicle": null,
      "driver_license": null,
      "pickup_address": "Koramangala, Bangalore",
      "pickup_lat": "12.935200",
      "pickup_lng": "77.614700",
      "dropoff_address": "MG Road, Bangalore",
      "drop_lat": "12.976300",
      "drop_lng": "77.603300",
      "status": "REQUESTED",
      "status_display": "Requested",
      "requested_at": "2025-10-03T20:00:00Z",
      "updated_at": "2025-10-03T20:00:00Z",
      "accepted_at": null,
      "completed_at": null,
      "estimated_fare": null,
      "final_fare": null
    }
  ]
}
```

**Notes:**
- Returns rides with `status='REQUESTED'` and `driver=null`
- Ordered by `requested_at` (oldest first) for fair allocation
- Empty list if no rides available

### 3. Accept Ride (Driver)
**Endpoint:** `POST /PerpexBistro/orders/ride/accept/<ride_id>/`

**Authentication:** JWT (Driver profile required)

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Ride accepted successfully",
  "ride": {
    "id": 1,
    "rider": 5,
    "rider_name": "john_rider",
    "rider_phone": "+1234567890",
    "driver": 10,
    "driver_name": "jane_driver",
    "driver_phone": "+0987654321",
    "driver_vehicle": "Camry",
    "driver_license": "ABC123XYZ",
    "pickup_address": "Koramangala, Bangalore",
    "pickup_lat": "12.935200",
    "pickup_lng": "77.614700",
    "dropoff_address": "MG Road, Bangalore",
    "drop_lat": "12.976300",
    "drop_lng": "77.603300",
    "status": "ONGOING",
    "status_display": "Ongoing",
    "requested_at": "2025-10-03T20:00:00Z",
    "updated_at": "2025-10-03T20:05:00Z",
    "accepted_at": "2025-10-03T20:05:00Z",
    "completed_at": null,
    "estimated_fare": null,
    "final_fare": null
  }
}
```

**Error Responses:**
- `404 Not Found` - Ride doesn't exist
- `400 Bad Request` - Ride already accepted or not in REQUESTED status
- `403 Forbidden` - User doesn't have driver profile

**Race Condition Prevention:**
Uses atomic transaction with `select_for_update()` to lock the ride row, ensuring only one driver can accept it.

## Usage Examples

### 1. Complete Workflow (Rider → Driver)

```python
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Setup
rider_token = str(RefreshToken.for_user(rider_user).access_token)
driver_token = str(RefreshToken.for_user(driver_user).access_token)

client = APIClient()

# Step 1: Rider requests ride
client.credentials(HTTP_AUTHORIZATION=f'Bearer {rider_token}')
response = client.post('/PerpexBistro/orders/ride/request/', {
    'pickup_address': 'Koramangala, Bangalore',
    'pickup_lat': 12.9352,
    'pickup_lng': 77.6147,
    'dropoff_address': 'MG Road, Bangalore',
    'drop_lat': 12.9763,
    'drop_lng': 77.6033
}, format='json')

ride_id = response.data['ride']['id']

# Step 2: Driver views available rides
client.credentials(HTTP_AUTHORIZATION=f'Bearer {driver_token}')
response = client.get('/PerpexBistro/orders/ride/available/')

# Step 3: Driver accepts the ride
response = client.post(f'/PerpexBistro/orders/ride/accept/{ride_id}/')
```

### 2. Direct Model Usage

```python
from orders.models import Ride, Rider, Driver
from decimal import Decimal

# Create a ride
ride = Ride.objects.create(
    rider=rider_instance,
    pickup_address='Location A',
    pickup_lat=Decimal('12.9352'),
    pickup_lng=Decimal('77.6147'),
    dropoff_address='Location B',
    drop_lat=Decimal('12.9763'),
    drop_lng=Decimal('77.6033')
)

# Accept the ride
ride.accept_ride(driver_instance)

# Complete the ride
ride.complete_ride(final_fare=Decimal('250.00'))

# Cancel the ride
ride.cancel_ride()
```

## Security Features

### 1. Authentication
- All endpoints require JWT authentication
- Tokens generated via `/PerpexBistro/orders/auth/login/`

### 2. Authorization
- Riders can only request rides (not accept)
- Drivers can only accept rides (not request)
- Profile validation in each view

### 3. Race Condition Prevention
```python
with transaction.atomic():
    ride = Ride.objects.select_for_update().get(pk=ride_id)
    if ride.status == Ride.STATUS_REQUESTED and ride.driver is None:
        ride.accept_ride(driver)
```

### 4. Data Validation
- Coordinate ranges: lat [-90, 90], lng [-180, 180]
- Pickup ≠ Dropoff validation
- Non-empty address validation
- Status transition rules enforced

## Database Indexes

```python
class Meta:
    indexes = [
        Index(fields=['status', 'requested_at']),  # Fast available rides query
        Index(fields=['rider', 'status']),          # Rider ride history
        Index(fields=['driver', 'status']),         # Driver ride history
    ]
```

## Logging

All views include comprehensive logging:
- Ride creation: `INFO` level
- Available rides queries: `INFO` level
- Ride acceptance: `INFO` level
- Errors: `ERROR` level with stack traces
- Unauthorized access: `WARNING` level

## Future Enhancements

### Already Prepared (fields exist):
- `estimated_fare` - Calculate before ride starts
- `final_fare` - Calculate after completion

### Suggested Future Features:
1. **Live Tracking** - Add current location updates
2. **ETA Calculation** - Estimate arrival times
3. **Fare Calculation** - Distance + time-based pricing
4. **Ride Ratings** - Rider/driver mutual ratings
5. **Ride History** - Endpoints for completed rides
6. **Cancellation Reasons** - Track why rides are cancelled
7. **Nearby Drivers** - Geographic filtering for available drivers
8. **Surge Pricing** - Dynamic pricing based on demand
9. **Multiple Stops** - Support for waypoints
10. **Ride Sharing** - Multiple riders in one ride

## Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test test_ride_booking

# Run with verbose output
python manage.py test test_ride_booking -v 2
```

### End-to-End Test Results
✅ Rider successfully requests ride
✅ Driver successfully views available rides  
✅ Driver successfully accepts ride
✅ Accepted ride no longer appears in available rides
✅ Race condition prevention working
✅ JWT authentication working
✅ Permission validation working

## Troubleshooting

### Common Issues

1. **"User does not have a rider/driver profile"**
   - Ensure user has associated Rider or Driver model instance
   - Check `request.user.rider_profile` or `request.user.driver_profile`

2. **"Ride already accepted"**
   - Race condition detected and prevented successfully
   - Another driver accepted first
   - This is expected behavior

3. **Coordinate validation errors**
   - Check lat/lng are within valid ranges
   - Ensure decimal precision matches field definition

4. **JWT authentication fails**
   - Check token is valid and not expired
   - Verify `Authorization: Bearer <token>` header format
   - Ensure token blacklist is not blocking token

## Performance Considerations

1. **Database Queries**
   - Indexed fields used in filtering (status, timestamps)
   - Atomic transactions keep locks minimal
   - select_for_update() only during acceptance

2. **Scalability**
   - Stateless JWT authentication (horizontal scaling ready)
   - Atomic operations prevent data corruption
   - Efficient ordering for fair allocation

3. **Monitoring**
   - Comprehensive logging for debugging
   - Track ride lifecycle with timestamps
   - Error codes for client handling

## Related Models

- **Rider** (`orders/models.py`) - User profile for ride requesters
- **Driver** (`orders/models.py`) - User profile for ride providers
- **User** (Django auth) - Base authentication model

## API Response Error Codes

- `NO_RIDER_PROFILE` - User attempting ride request without rider profile
- `NO_DRIVER_PROFILE` - User attempting driver action without driver profile  
- `RIDE_NOT_FOUND` - Requested ride ID doesn't exist
- `RIDE_NOT_AVAILABLE` - Ride not in REQUESTED status
- `RIDE_ALREADY_ACCEPTED` - Another driver already accepted
- `INVALID_DATA` - Validation errors in request
- `INTERNAL_ERROR` - Server error (check logs)

## Contact & Support

For questions or issues with the ride booking system:
- Check logs in Django console
- Review this documentation
- Check code comments in models.py, views.py, serializers.py
- Refer to Django REST Framework documentation

---

**Version:** 1.0  
**Last Updated:** October 3, 2025  
**Author:** Restaurant Management System Team
