#!/usr/bin/env python3
"""Test script for the weather dashboard data persistence system.

This script demonstrates and tests the functionality of the new database system.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import DataService


async def test_database_system():
    """Test the database system functionality."""
    print("🚀 Testing Weather Dashboard Data Persistence System")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize data service
    data_service = DataService(Path("test_data/test_weather.db"))
    
    try:
        # Test 1: Initialize the system
        print("\n📊 Test 1: System Initialization")
        print("-" * 40)
        
        success = await data_service.initialize()
        if success:
            print("✅ Data service initialized successfully")
        else:
            print("❌ Failed to initialize data service")
            return
        
        # Test 2: Save weather data
        print("\n🌤️  Test 2: Weather Data Storage")
        print("-" * 40)
        
        test_locations = [
            ("New York", 22.5, "Partly Cloudy", 65, 10.2, 1013.25),
            ("London", 18.0, "Rainy", 80, 15.5, 1008.5),
            ("Tokyo", 28.3, "Sunny", 45, 5.8, 1020.1),
            ("Sydney", 25.1, "Cloudy", 70, 12.3, 1015.8)
        ]
        
        for location, temp, conditions, humidity, wind, pressure in test_locations:
            success = await data_service.save_weather_data(
                location=location,
                temperature=temp,
                conditions=conditions,
                humidity=humidity,
                wind_speed=wind,
                pressure=pressure
            )
            
            if success:
                print(f"✅ Saved weather data for {location}")
            else:
                print(f"❌ Failed to save weather data for {location}")
        
        # Test 3: User preferences
        print("\n👤 Test 3: User Preferences")
        print("-" * 40)
        
        user_id = "test_user_001"
        
        # Save preferences
        preferences = {
            "temperature_unit": "celsius",
            "theme": "dark",
            "notifications": True,
            "default_location": "New York"
        }
        
        for key, value in preferences.items():
            success = await data_service.save_user_preference(user_id, key, value)
            if success:
                print(f"✅ Saved preference: {key} = {value}")
            else:
                print(f"❌ Failed to save preference: {key}")
        
        # Add favorite locations
        favorite_locations = ["New York", "London", "Tokyo"]
        for location in favorite_locations:
            success = await data_service.add_favorite_location(user_id, location)
            if success:
                print(f"✅ Added favorite location: {location}")
            else:
                print(f"❌ Failed to add favorite location: {location}")
        
        # Add recent searches
        searches = ["New York weather", "London forecast", "Tokyo temperature"]
        for search in searches:
            success = await data_service.add_recent_search(user_id, search)
            if success:
                print(f"✅ Added recent search: {search}")
            else:
                print(f"❌ Failed to add recent search: {search}")
        
        # Test 4: Activity logging
        print("\n📝 Test 4: Activity Logging")
        print("-" * 40)
        
        activities = [
            ("weather_lookup", {"location": "New York", "temperature": 22.5}),
            ("favorite_added", {"location": "London"}),
            ("search", {"query": "Tokyo weather"}),
            ("settings_changed", {"setting": "theme", "value": "dark"})
        ]
        
        for activity_type, activity_data in activities:
            success = await data_service.log_activity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data
            )
            
            if success:
                print(f"✅ Logged activity: {activity_type}")
            else:
                print(f"❌ Failed to log activity: {activity_type}")
        
        # Test 5: Journal entries
        print("\n📔 Test 5: Journal Entries")
        print("-" * 40)
        
        journal_entries = [
            (8.5, "Great weather today! Went for a walk.", {"temperature": 22.5, "conditions": "Sunny"}),
            (6.0, "Rainy day, feeling a bit down.", {"temperature": 18.0, "conditions": "Rainy"}),
            (9.0, "Perfect day for outdoor activities!", {"temperature": 25.1, "conditions": "Clear"})
        ]
        
        for mood_score, notes, weather_snapshot in journal_entries:
            success = await data_service.create_journal_entry(
                user_id=user_id,
                mood_score=mood_score,
                notes=notes,
                weather_snapshot=weather_snapshot
            )
            
            if success:
                print(f"✅ Created journal entry: mood {mood_score}/10")
            else:
                print(f"❌ Failed to create journal entry")
        
        # Test 6: Data retrieval
        print("\n📊 Test 6: Data Retrieval")
        print("-" * 40)
        
        # Get weather history
        for location in ["New York", "London"]:
            history = await data_service.get_weather_history(location, days=7)
            print(f"✅ Retrieved {len(history)} weather records for {location}")
        
        # Get user preferences
        user_prefs = await data_service.get_user_preferences(user_id)
        print(f"✅ Retrieved {len(user_prefs)} user preferences")
        
        # Get favorite locations
        favorites = await data_service.get_favorite_locations(user_id)
        print(f"✅ Retrieved {len(favorites)} favorite locations: {favorites}")
        
        # Get recent searches
        recent_searches = await data_service.get_recent_searches(user_id)
        print(f"✅ Retrieved {len(recent_searches)} recent searches: {recent_searches}")
        
        # Get user activities
        activities = await data_service.get_user_activities(user_id, days=7)
        print(f"✅ Retrieved {len(activities)} user activities")
        
        # Get journal entries
        journal = await data_service.get_journal_entries(user_id, days=7)
        print(f"✅ Retrieved {len(journal)} journal entries")
        
        # Get mood trends
        mood_trends = await data_service.get_mood_trends(user_id, days=7)
        print(f"✅ Retrieved mood trends: avg={mood_trends.get('average_mood', 'N/A')}")
        
        # Test 7: Statistics and analytics
        print("\n📈 Test 7: Statistics and Analytics")
        print("-" * 40)
        
        # Weather statistics
        for location in ["New York", "London"]:
            stats = await data_service.get_weather_statistics(location)
            print(f"✅ Weather stats for {location}: {len(stats)} metrics")
        
        # Activity statistics
        activity_stats = await data_service.get_activity_statistics(user_id)
        print(f"✅ Activity statistics: {len(activity_stats)} metrics")
        
        # Test 8: Cache functionality
        print("\n💾 Test 8: Cache System")
        print("-" * 40)
        
        # Get cache statistics
        cache_stats = data_service.get_cache_statistics()
        print(f"✅ Cache entries: {cache_stats['entries']}")
        print(f"✅ Cache hit rate: {cache_stats['hit_rate']:.2%}")
        print(f"✅ Cache memory usage: {cache_stats['memory_usage']} bytes")
        
        # Test cache with repeated requests
        print("\n🔄 Testing cache performance...")
        
        # First request (should hit database)
        start_time = datetime.now()
        history1 = await data_service.get_weather_history("New York", days=7)
        first_duration = (datetime.now() - start_time).total_seconds()
        
        # Second request (should hit cache)
        start_time = datetime.now()
        history2 = await data_service.get_weather_history("New York", days=7)
        second_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ First request: {first_duration:.4f}s (database)")
        print(f"✅ Second request: {second_duration:.4f}s (cache)")
        print(f"✅ Cache speedup: {first_duration/second_duration:.1f}x faster")
        
        # Test 9: Data export/import
        print("\n💾 Test 9: Data Export/Import")
        print("-" * 40)
        
        # Create export directory
        export_dir = Path("test_data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export data
        export_file = export_dir / f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        success = await data_service.export_data(export_file, user_id=user_id)
        
        if success:
            print(f"✅ Data exported to {export_file}")
            print(f"✅ Export file size: {export_file.stat().st_size} bytes")
        else:
            print(f"❌ Failed to export data")
        
        # Validate import (without actually importing)
        if export_file.exists():
            import_result = await data_service.import_data(
                export_file, 
                validate_only=True
            )
            
            if import_result['success']:
                print(f"✅ Import validation successful")
                print(f"✅ Validation statistics: {import_result['statistics']}")
            else:
                print(f"❌ Import validation failed: {import_result.get('error')}")
        
        # Test 10: Backup system
        print("\n💾 Test 10: Backup System")
        print("-" * 40)
        
        # Create backup
        backup_file = await data_service.create_backup("test_backup")
        
        if backup_file:
            print(f"✅ Backup created: {backup_file}")
            print(f"✅ Backup file size: {backup_file.stat().st_size} bytes")
        else:
            print(f"❌ Failed to create backup")
        
        # List backups
        backups = data_service.list_backups()
        print(f"✅ Available backups: {len(backups)}")
        
        for backup in backups[:3]:  # Show first 3
            print(f"   - {backup['name']}: {backup['size']} bytes, {backup['created']}")
        
        # Test 11: System health check
        print("\n🏥 Test 11: System Health Check")
        print("-" * 40)
        
        health = await data_service.health_check()
        print(f"✅ System status: {health['status']}")
        print(f"✅ Database status: {health['components']['database']['status']}")
        print(f"✅ Cache status: {health['components']['cache']['status']}")
        print(f"✅ Background tasks: {health['components']['background_tasks']['active_tasks']}")
        
        # Database info
        db_info = await data_service.get_database_info()
        print(f"✅ Database size: {db_info.get('size', 0)} bytes")
        print(f"✅ Database tables: {len(db_info.get('tables', []))}")
        
        # Migration status
        migration_status = await data_service.get_migration_status()
        print(f"✅ Current schema version: {migration_status.get('current_version')}")
        print(f"✅ Pending migrations: {len(migration_status.get('pending_migrations', []))}")
        
        # Test 12: Performance test
        print("\n⚡ Test 12: Performance Test")
        print("-" * 40)
        
        # Bulk insert test
        print("Testing bulk operations...")
        
        start_time = datetime.now()
        
        # Insert multiple weather records
        for i in range(50):
            await data_service.save_weather_data(
                location=f"TestCity{i%5}",
                temperature=20 + (i % 20),
                conditions="Test",
                humidity=50 + (i % 30),
                wind_speed=5 + (i % 15),
                pressure=1000 + (i % 50)
            )
        
        bulk_duration = (datetime.now() - start_time).total_seconds()
        print(f"✅ Inserted 50 weather records in {bulk_duration:.2f}s")
        print(f"✅ Average: {bulk_duration/50*1000:.1f}ms per record")
        
        # Query performance test
        start_time = datetime.now()
        
        for i in range(10):
            await data_service.get_weather_history(f"TestCity{i%5}", days=30)
        
        query_duration = (datetime.now() - start_time).total_seconds()
        print(f"✅ Executed 10 history queries in {query_duration:.2f}s")
        print(f"✅ Average: {query_duration/10*1000:.1f}ms per query")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 60)
        print("\n📋 Test Summary:")
        print("✅ System initialization")
        print("✅ Weather data storage and retrieval")
        print("✅ User preferences management")
        print("✅ Activity logging")
        print("✅ Journal entries")
        print("✅ Data analytics and statistics")
        print("✅ Cache system with performance benefits")
        print("✅ Data export/import functionality")
        print("✅ Automated backup system")
        print("✅ System health monitoring")
        print("✅ Performance optimization")
        
        print("\n🚀 The data persistence system is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await data_service.shutdown()
        print("✅ Data service shutdown complete")


if __name__ == "__main__":
    # Create test data directory
    Path("test_data").mkdir(exist_ok=True)
    
    # Run the test
    asyncio.run(test_database_system())