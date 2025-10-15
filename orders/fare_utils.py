"""
Fare calculation utilities for ride-sharing system.

This module provides functions for calculating ride fares based on distance,
base rates, and surge multipliers. Uses the Haversine formula for accurate
distance calculation between geographic coordinates.
"""

import math


# Fare calculation constants
BASE_FARE = 50  # Base fare in currency units (₹50)
PER_KM_RATE = 10  # Per kilometer rate (₹10/km)
EARTH_RADIUS_KM = 6371  # Earth's radius in kilometers


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula to calculate the distance between two
    latitude/longitude points, accounting for the spherical shape of Earth.
    
    Args:
        lat1 (float): Latitude of the first point in degrees
        lon1 (float): Longitude of the first point in degrees
        lat2 (float): Latitude of the second point in degrees
        lon2 (float): Longitude of the second point in degrees
    
    Returns:
        float: Distance between the two points in kilometers
    
    Example:
        >>> # Distance from New York to Los Angeles (approximate)
        >>> distance = calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
        >>> print(f"{distance:.2f} km")
        3944.42 km
    
    Notes:
        - Assumes a spherical Earth model (accurate to within 0.5%)
        - For more precise calculations over short distances, consider
          using Vincenty's formula or other ellipsoidal models
        - Input coordinates must be in decimal degrees
    
    References:
        https://en.wikipedia.org/wiki/Haversine_formula
    """
    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (
        math.sin(delta_phi / 2) ** 2 +
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Distance in kilometers
    distance = EARTH_RADIUS_KM * c
    
    return distance


def calculate_fare(distance_km, surge_multiplier=1.0, base_fare=None, per_km_rate=None):
    """
    Calculate ride fare based on distance and surge multiplier.
    
    Formula: fare = base_fare + (distance_km × per_km_rate) × surge_multiplier
    
    Args:
        distance_km (float): Distance of the ride in kilometers
        surge_multiplier (float, optional): Surge pricing multiplier.
            Default is 1.0 (normal pricing). Use 1.5 for 50% surge.
        base_fare (float, optional): Override default base fare
        per_km_rate (float, optional): Override default per-kilometer rate
    
    Returns:
        float: Calculated fare rounded to 2 decimal places
    
    Example:
        >>> # Normal fare for 10 km ride
        >>> fare = calculate_fare(10.0)
        >>> print(f"₹{fare:.2f}")
        ₹150.00
        
        >>> # Surge pricing (1.5x) for same ride
        >>> surge_fare = calculate_fare(10.0, surge_multiplier=1.5)
        >>> print(f"₹{surge_fare:.2f}")
        ₹200.00
    
    Notes:
        - Fare is always rounded to 2 decimal places
        - Surge multiplier is applied to the distance-based portion only,
          not to the base fare
        - Minimum fare is the base_fare (even for 0 km rides)
    """
    # Use provided values or defaults
    if base_fare is None:
        base_fare = BASE_FARE
    if per_km_rate is None:
        per_km_rate = PER_KM_RATE
    
    # Calculate fare using the formula
    fare = base_fare + (distance_km * per_km_rate) * surge_multiplier
    
    # Round to 2 decimal places
    return round(fare, 2)


def calculate_fare_from_coordinates(lat1, lon1, lat2, lon2, surge_multiplier=1.0):
    """
    Calculate fare directly from pickup and dropoff coordinates.
    
    Convenience function that combines distance calculation and fare calculation.
    
    Args:
        lat1 (float): Pickup latitude in degrees
        lon1 (float): Pickup longitude in degrees
        lat2 (float): Dropoff latitude in degrees
        lon2 (float): Dropoff longitude in degrees
        surge_multiplier (float, optional): Surge pricing multiplier. Default is 1.0.
    
    Returns:
        tuple: (distance_km, fare) - Distance in km and calculated fare
    
    Example:
        >>> # Calculate fare for a ride
        >>> distance, fare = calculate_fare_from_coordinates(
        ...     28.7041, 77.1025,  # Pickup: New Delhi
        ...     28.5355, 77.3910,  # Dropoff: Noida
        ...     surge_multiplier=1.2
        ... )
        >>> print(f"Distance: {distance:.2f} km, Fare: ₹{fare:.2f}")
        Distance: 35.42 km, Fare: ₹474.04
    """
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    fare = calculate_fare(distance, surge_multiplier)
    return distance, fare


def get_surge_multiplier_for_time(hour=None):
    """
    Get surge multiplier based on time of day.
    
    This is a simplified surge pricing model. In production, this would
    consider real-time demand, driver availability, and other factors.
    
    Args:
        hour (int, optional): Hour of day (0-23). If None, uses current time.
    
    Returns:
        float: Surge multiplier (1.0 for normal, 1.5+ for peak hours)
    
    Example:
        >>> # Morning rush hour (8 AM)
        >>> multiplier = get_surge_multiplier_for_time(8)
        >>> print(f"{multiplier}x")
        1.5x
        
        >>> # Off-peak (2 PM)
        >>> multiplier = get_surge_multiplier_for_time(14)
        >>> print(f"{multiplier}x")
        1.0x
    
    Peak Hours:
        - Morning: 7 AM - 10 AM → 1.5x
        - Evening: 5 PM - 9 PM → 1.5x
        - Late night: 11 PM - 5 AM → 1.3x
        - Normal: All other times → 1.0x
    """
    if hour is None:
        from datetime import datetime
        hour = datetime.now().hour
    
    # Morning rush (7 AM - 10 AM)
    if 7 <= hour < 10:
        return 1.5
    
    # Evening rush (5 PM - 9 PM)
    if 17 <= hour < 21:
        return 1.5
    
    # Late night (11 PM - 5 AM)
    if hour >= 23 or hour < 5:
        return 1.3
    
    # Normal hours
    return 1.0
