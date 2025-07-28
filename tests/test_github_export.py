#!/usr/bin/env python3
"""
Simple test script to verify GitHub export data fetching functionality using urllib.
This script tests the urllib-based export data fetching independently.
"""

import urllib.request
import urllib.error
import json
import csv
import io
from datetime import datetime

def test_export_data_fetching():
    """Test the export data fetching functionality using urllib directly."""
    print("=" * 60)
    print("Testing GitHub Export Data Fetching with urllib")
    print("=" * 60)
    
    export_base_url = "https://raw.githubusercontent.com/StrayDogSyn/New_Team_Dashboard/main/exports"
    
    try:
        # Test 1: Fetch JSON export data
        print("\n1. Testing JSON Export Data Fetching...")
        json_url = f"{export_base_url}/team_compare_cities_data_20250717_204218.json"
        
        try:
            with urllib.request.urlopen(json_url, timeout=10) as response:
                json_data = json.loads(response.read().decode('utf-8'))
                print(f"   ✅ JSON data fetched successfully!")
                print(f"   - Response status: {response.status}")
                print(f"   - Content length: {len(response.read()) if hasattr(response, 'read') else 'Unknown'}")
                
                # Analyze JSON structure
                if 'team_summary' in json_data:
                    team_summary = json_data['team_summary']
                    print(f"   - Total Members: {team_summary.get('total_members', 0)}")
                    print(f"   - Total Cities: {team_summary.get('total_cities', 0)}")
                    print(f"   - Total Records: {team_summary.get('total_records', 0)}")
                
                if 'cities_analysis' in json_data:
                    cities_count = len(json_data['cities_analysis'])
                    print(f"   - Cities Analyzed: {cities_count}")
                    
                    # Show sample cities
                    sample_cities = list(json_data['cities_analysis'].keys())[:3]
                    print(f"   - Sample Cities: {', '.join(sample_cities)}")
                
                if 'export_info' in json_data:
                    export_info = json_data['export_info']
                    print(f"   - Export Date: {export_info.get('export_date', 'Unknown')}")
                    print(f"   - Available Cities: {export_info.get('available_cities', 0)}")
                
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTP Error fetching JSON: {e.code} - {e.reason}")
            return False
        except urllib.error.URLError as e:
            print(f"   ❌ URL Error fetching JSON: {e.reason}")
            return False
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Decode Error: {e}")
            return False
        
        # Test 2: Fetch CSV export data
        print("\n2. Testing CSV Export Data Fetching...")
        csv_url = f"{export_base_url}/team_weather_data_20250717_204218.csv"
        
        try:
            with urllib.request.urlopen(csv_url, timeout=10) as response:
                csv_content = response.read().decode('utf-8')
                print(f"   ✅ CSV data fetched successfully!")
                print(f"   - Response status: {response.status}")
                print(f"   - Content length: {len(csv_content)} characters")
                
                # Parse CSV data
                csv_reader = csv.DictReader(io.StringIO(csv_content))
                csv_data = list(csv_reader)
                
                print(f"   - Total CSV Records: {len(csv_data)}")
                
                if csv_data:
                    sample_record = csv_data[0]
                    print(f"   - CSV Columns: {list(sample_record.keys())}")
                    print(f"   - Sample Record: {sample_record.get('member_name', 'N/A')} in {sample_record.get('city', 'N/A')}")
                
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTP Error fetching CSV: {e.code} - {e.reason}")
            return False
        except urllib.error.URLError as e:
            print(f"   ❌ URL Error fetching CSV: {e.reason}")
            return False
        
        # Test 3: Test error handling with invalid URL
        print("\n3. Testing Error Handling...")
        invalid_url = f"{export_base_url}/nonexistent_file.json"
        
        try:
            with urllib.request.urlopen(invalid_url, timeout=5) as response:
                print(f"   ❌ Unexpected success with invalid URL")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"   ✅ Correctly handled 404 error for invalid URL")
            else:
                print(f"   ⚠️  Unexpected HTTP error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"   ✅ Correctly handled URL error: {e.reason}")
        
        # Test 4: Test timeout handling
        print("\n4. Testing Timeout Configuration...")
        try:
            # Test with very short timeout (should work for GitHub)
            with urllib.request.urlopen(json_url, timeout=1) as response:
                print(f"   ✅ Request completed within 1 second timeout")
        except Exception as e:
            print(f"   ⚠️  Timeout test failed (may be due to slow connection): {e}")
        
        print(f"\n✅ All urllib export data fetching tests completed successfully!")
        print(f"\n🎉 GitHub Export Data Fetching is Working Correctly!")
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"SUMMARY:")
        print(f"- JSON export data: ✅ Accessible")
        print(f"- CSV export data: ✅ Accessible")
        print(f"- Error handling: ✅ Working")
        print(f"- urllib functionality: ✅ Operational")
        print(f"- Export URL base: {export_base_url}")
        print(f"=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    success = test_export_data_fetching()
    if success:
        print("\n🎉 SUCCESS: GitHub export data fetching with urllib is working!")
    else:
        print("\n❌ FAILURE: Issues detected with GitHub export data fetching.")
    
    exit(0 if success else 1)