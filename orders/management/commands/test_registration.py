from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from orders.models import Rider, Driver
from orders.serializers import RiderRegistrationSerializer, DriverRegistrationSerializer
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Test registration functionality with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Registration Functionality'))
        self.stdout.write('=' * 60)

        # Test Rider Registration
        self.stdout.write('\n📱 Testing Rider Registration...')
        rider_data = {
            'username': 'test_rider_cmd',
            'email': 'test_rider_cmd@example.com',
            'password': 'securepass123',
            'first_name': 'Test',
            'last_name': 'Rider',
            'phone': '+1234567890',
            'preferred_payment': 'card',
            'default_pickup_address': '123 Test Street',
            'default_pickup_latitude': 40.7128,
            'default_pickup_longitude': -74.0060,
        }

        try:
            # Clean up any existing user with same username/email
            User.objects.filter(username='test_rider_cmd').delete()
            User.objects.filter(email='test_rider_cmd@example.com').delete()
            
            serializer = RiderRegistrationSerializer(data=rider_data)
            if serializer.is_valid():
                user = serializer.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Rider created successfully: {user.username}'))
                self.stdout.write(f'   - User ID: {user.id}')
                self.stdout.write(f'   - Email: {user.email}')
                self.stdout.write(f'   - Rider Profile ID: {user.rider_profile.id}')
                self.stdout.write(f'   - Phone: {user.rider_profile.phone}')
                self.stdout.write(f'   - Payment Method: {user.rider_profile.preferred_payment}')
            else:
                self.stdout.write(self.style.ERROR('❌ Rider registration failed:'))
                for field, errors in serializer.errors.items():
                    self.stdout.write(f'   - {field}: {errors}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Rider registration exception: {e}'))

        # Test Driver Registration
        self.stdout.write('\n🚗 Testing Driver Registration...')
        driver_data = {
            'username': 'test_driver_cmd',
            'email': 'test_driver_cmd@example.com',
            'password': 'securepass123',
            'first_name': 'Test',
            'last_name': 'Driver',
            'phone': '+1987654321',
            'license_number': 'TESTCMD123',
            'license_expiry': (date.today() + timedelta(days=365)).isoformat(),
            'vehicle_make': 'Toyota',
            'vehicle_model': 'Camry',
            'vehicle_year': 2020,
            'vehicle_color': 'Silver',
            'vehicle_type': 'sedan',
            'license_plate': 'TESTCMD',
        }

        try:
            # Clean up any existing user with same username/email
            User.objects.filter(username='test_driver_cmd').delete()
            User.objects.filter(email='test_driver_cmd@example.com').delete()
            
            serializer = DriverRegistrationSerializer(data=driver_data)
            if serializer.is_valid():
                user = serializer.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Driver created successfully: {user.username}'))
                self.stdout.write(f'   - User ID: {user.id}')
                self.stdout.write(f'   - Email: {user.email}')
                self.stdout.write(f'   - Driver Profile ID: {user.driver_profile.id}')
                self.stdout.write(f'   - Phone: {user.driver_profile.phone}')
                self.stdout.write(f'   - License: {user.driver_profile.license_number}')
                self.stdout.write(f'   - Vehicle: {user.driver_profile.full_vehicle_name}')
                self.stdout.write(f'   - License Plate: {user.driver_profile.license_plate}')
            else:
                self.stdout.write(self.style.ERROR('❌ Driver registration failed:'))
                for field, errors in serializer.errors.items():
                    self.stdout.write(f'   - {field}: {errors}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Driver registration exception: {e}'))

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 SUMMARY')
        self.stdout.write('=' * 60)
        
        try:
            total_riders = Rider.objects.count()
            total_drivers = Driver.objects.count()
            total_users = User.objects.count()
            
            self.stdout.write(f'👥 Total Users: {total_users}')
            self.stdout.write(f'🛵 Total Riders: {total_riders}')
            self.stdout.write(f'🚗 Total Drivers: {total_drivers}')
            
            if total_riders > 0 and total_drivers > 0:
                self.stdout.write(self.style.SUCCESS('\n🎉 Registration functionality is working correctly!'))
            else:
                self.stdout.write(self.style.WARNING('\n⚠️ Some registration functionality may need attention.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error getting summary: {e}'))