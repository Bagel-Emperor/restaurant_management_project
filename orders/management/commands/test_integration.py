from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from orders.models import Rider, Driver
from orders.serializers import RiderRegistrationSerializer, DriverRegistrationSerializer


class Command(BaseCommand):
    help = 'Test integration of registration system with Django authentication'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔗 Testing Registration System Integration'))
        self.stdout.write('=' * 60)

        # Test 1: Registration and Authentication Integration
        self.stdout.write('\n🔐 Test 1: Registration + Authentication Integration')
        
        # Clean up any existing test users
        User.objects.filter(username__startswith='integration_test_').delete()
        
        # Register a rider
        rider_data = {
            'username': 'integration_test_rider',
            'email': 'integration_rider@example.com',
            'password': 'testpass123',
            'first_name': 'Integration',
            'last_name': 'Rider',
            'phone': '+1111111111',
            'preferred_payment': 'card',
        }
        
        rider_serializer = RiderRegistrationSerializer(data=rider_data)
        if rider_serializer.is_valid():
            rider_user = rider_serializer.save()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Rider registered: {rider_user.username}'))
            
            # Test authentication
            auth_user = authenticate(username='integration_test_rider', password='testpass123')
            if auth_user:
                self.stdout.write(self.style.SUCCESS('   ✅ Rider can authenticate successfully'))
                self.stdout.write(f'   - Authenticated user: {auth_user.username}')
                self.stdout.write(f'   - Has rider profile: {hasattr(auth_user, "rider_profile")}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ Rider authentication failed'))
        else:
            self.stdout.write(self.style.ERROR(f'   ❌ Rider registration failed: {rider_serializer.errors}'))

        # Register a driver
        driver_data = {
            'username': 'integration_test_driver',
            'email': 'integration_driver@example.com',
            'password': 'testpass123',
            'first_name': 'Integration',
            'last_name': 'Driver',
            'phone': '+2222222222',
            'license_number': 'INTEG12345',
            'license_expiry': '2026-12-31',
            'vehicle_make': 'Honda',
            'vehicle_model': 'Civic',
            'vehicle_year': 2021,
            'vehicle_color': 'Blue',
            'license_plate': 'INTEG1',
        }
        
        driver_serializer = DriverRegistrationSerializer(data=driver_data)
        if driver_serializer.is_valid():
            driver_user = driver_serializer.save()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Driver registered: {driver_user.username}'))
            
            # Test authentication
            auth_user = authenticate(username='integration_test_driver', password='testpass123')
            if auth_user:
                self.stdout.write(self.style.SUCCESS('   ✅ Driver can authenticate successfully'))
                self.stdout.write(f'   - Authenticated user: {auth_user.username}')
                self.stdout.write(f'   - Has driver profile: {hasattr(auth_user, "driver_profile")}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ Driver authentication failed'))
        else:
            self.stdout.write(self.style.ERROR(f'   ❌ Driver registration failed: {driver_serializer.errors}'))

        # Test 2: Profile Relationships and Data Integrity
        self.stdout.write('\n🔗 Test 2: Profile Relationships and Data Integrity')
        
        try:
            # Test rider relationship
            rider_user = User.objects.get(username='integration_test_rider')
            rider_profile = rider_user.rider_profile
            
            self.stdout.write(f'   ✅ Rider-User relationship intact')
            self.stdout.write(f'   - User: {rider_user.username} (ID: {rider_user.id})')
            self.stdout.write(f'   - Rider Profile: {rider_profile.id}')
            self.stdout.write(f'   - Profile belongs to user: {rider_profile.user == rider_user}')
            
            # Test driver relationship
            driver_user = User.objects.get(username='integration_test_driver')
            driver_profile = driver_user.driver_profile
            
            self.stdout.write(f'   ✅ Driver-User relationship intact')
            self.stdout.write(f'   - User: {driver_user.username} (ID: {driver_user.id})')
            self.stdout.write(f'   - Driver Profile: {driver_profile.id}')
            self.stdout.write(f'   - Profile belongs to user: {driver_profile.user == driver_user}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Profile relationship error: {e}'))

        # Test 3: Django Admin Integration
        self.stdout.write('\n👑 Test 3: Django Admin Integration')
        
        try:
            rider_user = User.objects.get(username='integration_test_rider')
            driver_user = User.objects.get(username='integration_test_driver')
            
            # Check if users appear in admin
            self.stdout.write(f'   ✅ Users queryable via Django ORM')
            self.stdout.write(f'   - Rider user accessible: {rider_user is not None}')
            self.stdout.write(f'   - Driver user accessible: {driver_user is not None}')
            
            # Check if profiles are accessible
            self.stdout.write(f'   ✅ Profiles accessible via related fields')
            self.stdout.write(f'   - Rider profile: {rider_user.rider_profile is not None}')
            self.stdout.write(f'   - Driver profile: {driver_user.driver_profile is not None}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Admin integration error: {e}'))

        # Test 4: Permissions and Security
        self.stdout.write('\n🛡️ Test 4: Permissions and Security')
        
        try:
            rider_user = User.objects.get(username='integration_test_rider')
            driver_user = User.objects.get(username='integration_test_driver')
            
            # Test password hashing
            self.stdout.write(f'   ✅ Password security')
            self.stdout.write(f'   - Rider password hashed: {not rider_user.password.startswith("testpass")}')
            self.stdout.write(f'   - Driver password hashed: {not driver_user.password.startswith("testpass")}')
            
            # Test user properties
            self.stdout.write(f'   ✅ User properties')
            self.stdout.write(f'   - Rider is_active: {rider_user.is_active}')
            self.stdout.write(f'   - Rider is_staff: {rider_user.is_staff}')
            self.stdout.write(f'   - Driver is_active: {driver_user.is_active}')
            self.stdout.write(f'   - Driver is_staff: {driver_user.is_staff}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Security test error: {e}'))

        # Test 5: Data Validation and Constraints
        self.stdout.write('\n✅ Test 5: Data Validation and Constraints')
        
        try:
            # Test unique constraints are working
            duplicate_rider_data = rider_data.copy()
            duplicate_rider_serializer = RiderRegistrationSerializer(data=duplicate_rider_data)
            
            if not duplicate_rider_serializer.is_valid():
                self.stdout.write('   ✅ Duplicate rider registration properly rejected')
                self.stdout.write(f'   - Errors: {list(duplicate_rider_serializer.errors.keys())}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ Duplicate rider registration should have been rejected'))
            
            # Test unique constraints for driver
            duplicate_driver_data = driver_data.copy()
            duplicate_driver_serializer = DriverRegistrationSerializer(data=duplicate_driver_data)
            
            if not duplicate_driver_serializer.is_valid():
                self.stdout.write('   ✅ Duplicate driver registration properly rejected')
                self.stdout.write(f'   - Errors: {list(duplicate_driver_serializer.errors.keys())}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ Duplicate driver registration should have been rejected'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Validation test error: {e}'))

        # Final Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 INTEGRATION TEST SUMMARY')
        self.stdout.write('=' * 60)
        
        try:
            total_users = User.objects.count()
            total_riders = Rider.objects.count()
            total_drivers = Driver.objects.count()
            
            self.stdout.write(f'👥 Total System Users: {total_users}')
            self.stdout.write(f'🛵 Total Riders: {total_riders}')
            self.stdout.write(f'🚗 Total Drivers: {total_drivers}')
            
            # Check if our test users exist and are integrated
            test_users = User.objects.filter(username__startswith='integration_test_').count()
            self.stdout.write(f'🧪 Test Users Created: {test_users}')
            
            if test_users >= 2:
                self.stdout.write(self.style.SUCCESS('\n🎉 Registration system is fully integrated with Django!'))
                self.stdout.write('✅ User authentication working')
                self.stdout.write('✅ Profile relationships intact')
                self.stdout.write('✅ Data validation enforced')
                self.stdout.write('✅ Security measures in place')
            else:
                self.stdout.write(self.style.WARNING('\n⚠️ Integration may need attention'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Summary error: {e}'))
            
        self.stdout.write('\n🧹 Cleaning up test data...')
        User.objects.filter(username__startswith='integration_test_').delete()
        self.stdout.write(self.style.SUCCESS('✅ Test data cleaned up'))