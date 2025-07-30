import os
import sqlite3
from datetime import datetime
from pathlib import Path

db_path = Path("data/weather_dashboard.db")
print(f"🗄️  Database file: {db_path}")
print(f"📁 File exists: {db_path.exists()}")

if db_path.exists():
    print(f"📊 File size: {db_path.stat().st_size: ,} bytes")
    print(f"📅 Last modified: {datetime.fromtimestamp(db_path.stat().st_mtime)}")

    # Connect and check tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📋 Tables in database: {[table[0] for table in tables]}")

    # Check record counts
    print("\n📊 Record counts:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  - {table_name}: {count} records")

    # Show some sample data from weather_history
    if ("weather_history",) in tables:
        print("\n🌤️  Latest weather entries:")
        cursor.execute(
            "SELECT city_name, temperature, condition, timestamp FROM weather_history ORDER BY timestamp DESC LIMIT 3"
        )
        rows = cursor.fetchall()
        for row in rows:
            print(f"  - {row[0]}: {row[1]}°C, {row[2]} at {row[3]}")

    # Show user preferences
    if ("user_preferences",) in tables:
        print("\n⚙️  User preferences:")
        cursor.execute(
            "SELECT activity_types, preferred_units, cache_enabled FROM user_preferences LIMIT 1"
        )
        prefs = cursor.fetchone()
        if prefs:
            print(f"  - Activity types: {prefs[0]}")
            print(f"  - Units: {prefs[1]}")
            print(f"  - Cache enabled: {prefs[2]}")

    # Show favorite cities
    if ("favorite_cities",) in tables:
        print("\n🏙️  Favorite cities:")
        cursor.execute("SELECT city_name, country_code FROM favorite_cities LIMIT 5")
        cities = cursor.fetchall()
        for city in cities:
            print(f"  - {city[0]}, {city[1]}")

    conn.close()
    print("\n✅ Database inspection completed successfully!")
else:
    print("❌ Database file not found!")
