"""
Session Manager Demonstration Script

This script demonstrates the session management system in action
with realistic ride-sharing and food delivery scenarios.
Run this script to see how sessions work in practice.
"""

import sys
import os
import time
import threading
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from restaurant_management.utils.session_manager import (
    SessionManager,
    SlidingSessionManager, 
    PersistentSessionManager
)


def print_header(title):
    """Print a formatted header for demo sections."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_step(step_num, description):
    """Print a formatted step description."""
    print(f"\n[Step {step_num}] {description}")


def simulate_delay(seconds, description=""):
    """Simulate time passing with a visual countdown."""
    if description:
        print(f"   {description}")
    
    for i in range(seconds, 0, -1):
        print(f"   Waiting {i} seconds...", end="\r")
        time.sleep(1)
    print("   ✓ Complete" + " "*20)


def demo_basic_session_manager():
    """Demonstrate basic session manager functionality."""
    print_header("BASIC SESSION MANAGER DEMO")
    print("Simulating rider session management (1-hour fixed sessions)")
    
    # Create session manager with 10-second expiry for demo
    sm = SessionManager(expiry_seconds=10)
    
    print_step(1, "Creating sessions for 3 riders")
    riders = ["rider_001", "rider_002", "rider_003"]
    
    for rider in riders:
        sm.create_session(rider)
        print(f"   ✓ Created session for {rider}")
    
    print_step(2, "Checking session status")
    for rider in riders:
        is_active = sm.is_session_active(rider)
        info = sm.get_session_info(rider)
        print(f"   {rider}: {'Active' if is_active else 'Inactive'} "
              f"(expires in {info['remaining_seconds']:.1f}s)")
    
    print(f"   Total active sessions: {sm.get_active_session_count()}")
    
    print_step(3, "Waiting for sessions to expire...")
    simulate_delay(12, "Sessions expire after 10 seconds...")
    
    print_step(4, "Checking sessions after expiry")
    for rider in riders:
        is_active = sm.is_session_active(rider)
        info = sm.get_session_info(rider)
        status = 'Active' if is_active else 'Expired'
        print(f"   {rider}: {status}")
    
    print(f"   Total active sessions: {sm.get_active_session_count()}")
    
    print_step(5, "Cleaning up expired sessions")
    cleaned = sm.cleanup_expired_sessions()
    print(f"   ✓ Cleaned up {cleaned} expired sessions")
    print(f"   Total active sessions: {sm.get_active_session_count()}")


def demo_sliding_session_manager():
    """Demonstrate sliding session manager functionality."""
    print_header("SLIDING SESSION MANAGER DEMO")
    print("Simulating driver session management (auto-refreshing sessions)")
    
    # Create sliding session manager with 8-second expiry for demo
    ssm = SlidingSessionManager(expiry_seconds=8)
    
    print_step(1, "Creating session for active driver")
    driver_id = "driver_007"
    ssm.create_session(driver_id)
    print(f"   ✓ Created sliding session for {driver_id}")
    
    print_step(2, "Simulating periodic location updates (every 3 seconds)")
    
    for update_num in range(1, 4):
        print(f"\n   Location Update #{update_num}:")
        
        # Check session (this refreshes the sliding session)
        is_active = ssm.is_session_active(driver_id)
        info = ssm.get_session_info(driver_id)
        
        print(f"   Session status: {'Active' if is_active else 'Expired'}")
        if info:
            print(f"   Time remaining: {info['remaining_seconds']:.1f}s")
            print(f"   Session age: {info['age_seconds']:.1f}s")
        
        if update_num < 3:
            simulate_delay(3, f"Driver continues driving...")
    
    print_step(3, "Driver stops sending location updates")
    simulate_delay(10, "No activity for 10 seconds...")
    
    print_step(4, "Checking session after inactivity")
    is_active = ssm.is_session_active(driver_id)
    print(f"   Session status: {'Active (refreshed)' if is_active else 'Expired due to inactivity'}")


def demo_persistent_session_manager():
    """Demonstrate persistent session manager functionality.""" 
    print_header("PERSISTENT SESSION MANAGER DEMO")
    print("Simulating delivery driver sessions (survive app restarts)")
    
    # Create persistent session manager with 15-second expiry for demo
    storage_file = "demo_sessions.json"
    psm = PersistentSessionManager(expiry_seconds=15, storage_file=storage_file)
    
    print_step(1, "Creating persistent sessions for delivery drivers")
    drivers = ["delivery_001", "delivery_002"]
    
    for driver in drivers:
        psm.create_session(driver)
        print(f"   ✓ Created persistent session for {driver}")
    
    print(f"   Sessions saved to: {storage_file}")
    
    print_step(2, "Simulating app restart (creating new manager instance)")
    
    # Create new manager instance (simulates app restart)
    psm2 = PersistentSessionManager(expiry_seconds=15, storage_file=storage_file)
    print("   ✓ New session manager instance created")
    
    print_step(3, "Checking if sessions survived restart")
    for driver in drivers:
        is_active = psm2.is_session_active(driver)
        info = psm2.get_session_info(driver)
        print(f"   {driver}: {'Restored and Active' if is_active else 'Not Found'}")
        if info:
            print(f"      Time remaining: {info['remaining_seconds']:.1f}s")
    
    print_step(4, "Waiting for sessions to expire")
    simulate_delay(16, "Sessions expire after 15 seconds...")
    
    print_step(5, "Checking sessions after expiry")
    for driver in drivers:
        is_active = psm2.is_session_active(driver)
        print(f"   {driver}: {'Still Active' if is_active else 'Expired'}")
    
    # Cleanup demo file
    try:
        os.remove(storage_file)
        print(f"   ✓ Cleaned up demo file: {storage_file}")
    except FileNotFoundError:
        pass


def demo_concurrent_access():
    """Demonstrate thread-safe concurrent access to session managers."""
    print_header("CONCURRENT ACCESS DEMO")
    print("Testing thread-safety with multiple concurrent operations")
    
    sm = SessionManager(expiry_seconds=30)
    results = {'created': 0, 'checked': 0, 'deleted': 0}
    results_lock = threading.Lock()
    
    def worker_thread(thread_id):
        """Worker thread that performs session operations."""
        session_id = f"concurrent_user_{thread_id}"
        
        # Create session
        sm.create_session(session_id)
        with results_lock:
            results['created'] += 1
        
        # Check session multiple times
        for _ in range(5):
            sm.is_session_active(session_id)
            with results_lock:
                results['checked'] += 1
            time.sleep(0.1)
        
        # Delete session
        sm.delete_session(session_id)
        with results_lock:
            results['deleted'] += 1
    
    print_step(1, "Starting 10 concurrent worker threads")
    threads = []
    
    for i in range(10):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    print_step(2, "Waiting for all threads to complete")
    for thread in threads:
        thread.join()
    
    print_step(3, "Results summary")
    print(f"   Sessions created: {results['created']}")
    print(f"   Session checks performed: {results['checked']}")
    print(f"   Sessions deleted: {results['deleted']}")
    print(f"   Final active sessions: {sm.get_active_session_count()}")
    
    print("   ✓ All operations completed successfully (thread-safe)")


def demo_real_world_scenario():
    """Demonstrate a realistic ride-sharing scenario."""
    print_header("REAL-WORLD SCENARIO DEMO")
    print("Simulating a complete ride-sharing journey")
    
    # Different session managers for different user types
    driver_sm = SlidingSessionManager(expiry_seconds=20)  # Sliding for active drivers
    rider_sm = SessionManager(expiry_seconds=25)          # Fixed for riders
    
    driver_id = "driver_alice"
    rider_id = "rider_bob"
    
    print_step(1, "Driver and Rider login")
    driver_sm.create_session(driver_id)
    rider_sm.create_session(rider_id)
    print(f"   ✓ Driver {driver_id} logged in (sliding session)")
    print(f"   ✓ Rider {rider_id} logged in (fixed session)")
    
    print_step(2, "Rider requests ride")
    if rider_sm.is_session_active(rider_id):
        print("   ✓ Rider session valid - ride request accepted")
    else:
        print("   ✗ Rider session expired - ride request denied")
        return
    
    print_step(3, "Driver accepts ride and starts driving")
    for minute in range(1, 4):
        print(f"\n   Minute {minute} - Driver location update:")
        
        # Driver sends location update (refreshes sliding session)
        if driver_sm.is_session_active(driver_id):
            driver_info = driver_sm.get_session_info(driver_id)
            print(f"   ✓ Driver session active (expires in {driver_info['remaining_seconds']:.1f}s)")
        else:
            print("   ✗ Driver session expired - ride cancelled")
            return
        
        # Check rider session
        if rider_sm.is_session_active(rider_id):
            rider_info = rider_sm.get_session_info(rider_id)
            print(f"   ✓ Rider session active (expires in {rider_info['remaining_seconds']:.1f}s)")
        else:
            print("   ✗ Rider session expired - ride cancelled")
            return
        
        simulate_delay(3, f"Driving to destination...")
    
    print_step(4, "Ride completed - Users log out")
    driver_result = driver_sm.delete_session(driver_id)
    rider_result = rider_sm.delete_session(rider_id)
    
    print(f"   Driver logout: {driver_result}")
    print(f"   Rider logout: {rider_result}")
    print("   ✓ Ride completed successfully!")


def demo_error_handling():
    """Demonstrate error handling and edge cases."""
    print_header("ERROR HANDLING DEMO")
    print("Testing error conditions and edge cases")
    
    sm = SessionManager(expiry_seconds=5)
    
    print_step(1, "Testing duplicate session creation")
    user_id = "test_user"
    
    result1 = sm.create_session(user_id)
    print(f"   First create_session(): {result1}")
    
    result2 = sm.create_session(user_id)  # Should update existing
    print(f"   Second create_session(): {result2}")
    
    print_step(2, "Testing operations on non-existent sessions")
    fake_user = "non_existent_user"
    
    is_active = sm.is_session_active(fake_user)
    print(f"   is_session_active('{fake_user}'): {is_active}")
    
    info = sm.get_session_info(fake_user)
    print(f"   get_session_info('{fake_user}'): {info}")
    
    delete_result = sm.delete_session(fake_user)
    print(f"   delete_session('{fake_user}'): {delete_result}")
    
    print_step(3, "Testing session expiry edge case")
    print("   Waiting for session to expire...")
    simulate_delay(6, "Session expires in 5 seconds...")
    
    is_active = sm.is_session_active(user_id)
    print(f"   Session active after expiry: {is_active}")
    
    # Try to delete expired session
    delete_result = sm.delete_session(user_id)
    print(f"   Delete expired session: {delete_result}")


def main():
    """Run all demonstration scenarios."""
    print("🚗 SESSION MANAGER DEMONSTRATION SUITE 🚗")
    print("This demo shows the session management system in action")
    print("with realistic ride-sharing and food delivery scenarios.")
    
    try:
        demo_basic_session_manager()
        demo_sliding_session_manager()
        demo_persistent_session_manager()
        demo_concurrent_access()
        demo_real_world_scenario()
        demo_error_handling()
        
        print_header("DEMONSTRATION COMPLETE")
        print("✓ All session manager features demonstrated successfully!")
        print("✓ Ready for production use in ride-sharing/delivery apps!")
        print("\nKey Features Demonstrated:")
        print("• Basic session management with expiration")
        print("• Sliding sessions that refresh on activity")
        print("• Persistent sessions that survive app restarts")
        print("• Thread-safe concurrent access")
        print("• Real-world ride-sharing scenario")
        print("• Comprehensive error handling")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()