# Driver Earnings and Availability Features - Tasks 12A, 12B, 13A, 13B

## Overview
Complete implementation of driver earnings summary and availability toggle features for the restaurant management system's driver portal.

## Features Implemented

### Task 12A: DriverEarningsSerializer
**Purpose:** Serialize driver's weekly earnings data
- **Location:** `orders/serializers.py` (lines 1182-1327)
- **Features:**
  - Total rides count (last 7 days, completed, paid)
  - Total earnings (sum of fares)
  - Payment breakdown by method (CASH/UPI/CARD)
  - Average fare (rounded to 2 decimals)
- **Tests:** 9 unit tests in `tests/test_driver_earnings_availability.py`

### Task 12B: DriverEarningsSummaryView
**Purpose:** REST API endpoint to retrieve driver earnings
- **Location:** `orders/views.py` (lines 1750-1806)
- **Endpoint:** `GET /PerpexBistro/orders/driver/earnings/`
- **Authentication:** Required (IsAuthenticated)
- **Permissions:** Driver profile required (403 if not)
- **Response:** JSON with earnings data
- **Tests:** 8 integration tests in `tests/test_driver_earnings_availability_views.py`

### Task 13A: DriverAvailabilitySerializer
**Purpose:** Serialize and validate availability toggle requests
- **Location:** `orders/serializers.py` (lines 1329-1443)
- **Features:**
  - Boolean `is_available` input field
  - Read-only `availability_status` output
  - Maps True → 'available', False → 'offline'
  - Validates authentication and driver profile
- **Tests:** 7 unit tests in `tests/test_driver_earnings_availability.py`

### Task 13B: DriverAvailabilityToggleView
**Purpose:** REST API endpoint to toggle driver availability
- **Location:** `orders/views.py` (lines 1809-1893)
- **Endpoint:** `POST /PerpexBistro/orders/driver/availability/`
- **Authentication:** Required (IsAuthenticated)
- **Request Body:** `{"is_available": true/false}`
- **Response:** `{"is_available": bool, "availability_status": str}`
- **Tests:** 8 integration tests in `tests/test_driver_earnings_availability_views.py`

## API Usage Examples

### Get Driver Earnings
```bash
curl -X GET http://localhost:8000/PerpexBistro/orders/driver/earnings/ \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Response:**
```json
{
  "total_rides": 18,
  "total_earnings": "4850.00",
  "payment_breakdown": {
    "CASH": 8,
    "UPI": 6,
    "CARD": 4
  },
  "average_fare": "269.44"
}
```

### Toggle Driver Availability
```bash
curl -X POST http://localhost:8000/PerpexBistro/orders/driver/availability/ \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"is_available": true}'
```

**Response:**
```json
{
  "is_available": true,
  "availability_status": "available"
}
```

## Test Coverage

### Unit Tests (15 total)
- **DriverEarningsSerializer:** 9 tests
  - No rides scenario
  - Single/multiple rides
  - Payment method filtering
  - Ride status filtering (COMPLETED only)
  - Payment status filtering (PAID only)
  - 7-day time window
  - Average fare rounding
  - Realistic scenario

- **DriverAvailabilitySerializer:** 7 tests
  - Toggle offline → available
  - Toggle available → offline
  - Authentication validation
  - Driver profile validation
  - Required field validation
  - Multiple toggles
  - Status representation

### Integration Tests (15 total)
- **DriverEarningsSummaryView:** 8 tests
  - Unauthenticated access (401)
  - Non-driver user (403)
  - No rides scenario
  - Multiple rides
  - Unpaid rides filtering
  - Incomplete rides filtering
  - Time window filtering
  - Response data validation

- **DriverAvailabilityToggleView:** 8 tests
  - Unauthenticated access (401)
  - Non-driver user (400)
  - Missing field (400)
  - Toggle to available (200)
  - Toggle to offline (200)
  - Multiple toggles
  - Invalid value (400)
  - Response format validation

**Total Tests:** 30 (all passing ✅)

## Files Modified

1. **orders/serializers.py**
   - Added DriverEarningsSerializer (lines 1182-1327)
   - Added DriverAvailabilitySerializer (lines 1329-1443)

2. **orders/views.py**
   - Imported new serializers
   - Added DriverEarningsSummaryView (lines 1750-1806)
   - Added DriverAvailabilityToggleView (lines 1809-1893)

3. **orders/urls.py**
   - Imported new views
   - Added driver/earnings/ URL pattern
   - Added driver/availability/ URL pattern

4. **tests/test_driver_earnings_availability.py** (new file)
   - 15 unit tests for serializers

5. **tests/test_driver_earnings_availability_views.py** (new file)
   - 15 integration tests for views

## Technical Details

### Dependencies
- Django 5.2.5
- Django REST Framework
- Python Decimal for financial precision
- Django ORM aggregation (Sum, Avg, Count)

### Database
- Uses existing Driver and Ride models
- No new migrations required
- Relies on simplified availability_status (offline/available)

### Key Patterns
- SerializerMethodField for computed values
- APIView for class-based views
- Permission classes for authentication
- Context passing for request data
- Comprehensive error handling and logging
- Decimal quantization for financial data

## Commits

1. **f2540c2** - feat: add driver earnings and availability serializers (Tasks 12A, 13A)
   - Added both serializers with comprehensive docstrings
   - 15 unit tests (all passing)
   - Fixed authentication edge case

2. **b3e4878** - feat: add driver earnings and availability API views (Tasks 12B, 13B)
   - Added both API views with error handling
   - 15 integration tests (all passing)
   - URL configuration
   - Proper logging throughout

## Usage in Driver Portal

### Earnings Dashboard
Drivers can view their weekly performance:
- "You completed 18 rides this week"
- "Total earnings: ₹4,850.00"
- "Average fare: ₹269.44"
- "Payment breakdown: 8 cash, 6 UPI, 4 card"

### Availability Toggle
Drivers can go online/offline:
- Toggle switch in mobile app
- "Go Online" button → POST {is_available: true}
- "Go Offline" button → POST {is_available: false}
- Real-time status display

## Future Enhancements
- Caching for earnings data (Redis)
- WebSocket for real-time availability updates
- Push notifications for status changes
- Admin dashboard for monitoring driver availability
- Historical earnings trends (monthly/yearly)
- Detailed ride-by-ride breakdown
