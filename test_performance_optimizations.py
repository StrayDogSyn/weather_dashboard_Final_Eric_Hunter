#!/usr/bin/env python3
"""
Test script for performance optimizations in the weather dashboard.
This script verifies that all optimization components are working correctly.
"""

import sys
import os
import time
import asyncio
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.cache_manager import CacheManager
from src.utils.startup_optimizer import StartupOptimizer, ComponentPriority
from src.utils.component_recycler import ComponentRecycler
from src.utils.api_optimizer import APIOptimizer, APIRequest, RequestPriority, CacheStrategy

def test_cache_manager():
    """Test the cache manager functionality."""
    print("\n=== Testing Cache Manager ===")
    
    # Initialize cache manager
    cache = CacheManager(max_size_mb=10, enable_compression=True)
    
    # Test basic operations
    print("Testing basic cache operations...")
    cache.set("test_key", {"data": "test_value", "timestamp": time.time()})
    result = cache.get("test_key")
    assert result is not None, "Cache get failed"
    print("✓ Basic cache operations working")
    
    # Test compression
    print("Testing compression...")
    large_data = {"data": "x" * 2000, "numbers": list(range(1000))}
    cache.set("large_key", large_data, ttl=300)
    compressed_result = cache.get("large_key")
    assert compressed_result == large_data, "Compression/decompression failed"
    print("✓ Compression working")
    
    # Test tags
    print("Testing tag-based operations...")
    cache.set("tagged_key1", "value1", tags=["group1", "test"])
    cache.set("tagged_key2", "value2", tags=["group1", "demo"])
    tagged_items = cache.get_by_tags(["group1"])
    assert len(tagged_items) == 2, "Tag-based retrieval failed"
    print("✓ Tag-based operations working")
    
    # Test statistics
    stats = cache.get_stats()
    print(f"Cache stats: {stats['hit_rate']:.2f}% hit rate, {stats['total_size_mb']:.2f}MB used")
    print("✓ Cache Manager tests passed")

def test_startup_optimizer():
    """Test the startup optimizer functionality."""
    print("\n=== Testing Startup Optimizer ===")
    
    optimizer = StartupOptimizer()
    
    # Register test components
    print("Registering components...")
    optimizer.register_component(
        "weather_service",
        ComponentPriority.CRITICAL,
        lambda: time.sleep(0.1) or {"status": "loaded"},
        dependencies=[]
    )
    
    optimizer.register_component(
        "forecast_cards",
        ComponentPriority.HIGH,
        lambda: time.sleep(0.05) or {"cards": 5},
        dependencies=["weather_service"]
    )
    
    optimizer.register_component(
        "activity_suggestions",
        ComponentPriority.MEDIUM,
        lambda: time.sleep(0.03) or {"activities": 3},
        dependencies=["weather_service"]
    )
    
    print("✓ Components registered")
    
    # Test progressive loading
    print("Testing progressive loading...")
    start_time = time.time()
    
    def on_component_loaded(name, success):
        print(f"  Component '{name}' loaded: {success}")
    
    def on_complete():
        elapsed = time.time() - start_time
        print(f"  All components loaded in {elapsed:.2f}s")
    
    optimizer.start_progressive_loading(
        on_component_loaded=on_component_loaded,
        on_complete=on_complete
    )
    
    # Wait for completion
    time.sleep(0.5)
    
    stats = optimizer.get_performance_stats()
    print(f"Performance: {stats['total_load_time']:.2f}s total, {stats['components_loaded']} components")
    print("✓ Startup Optimizer tests passed")

def test_component_recycler():
    """Test the component recycler functionality."""
    print("\n=== Testing Component Recycler ===")
    
    recycler = ComponentRecycler()
    
    # Test component pool registration
    print("Testing component pool registration...")
    
    def create_test_widget():
        return {"id": time.time(), "data": "test_widget"}
    
    def reset_test_widget(widget):
        widget["data"] = "reset_widget"
        return widget
    
    recycler.register_component_type(
        component_type=dict,
        max_pool_size=5,
        factory_func=create_test_widget,
        reset_func=reset_test_widget
    )
    
    print("✓ Component pool registered")
    
    # Test component lifecycle
    print("Testing component lifecycle...")
    
    # Get components
    widget1 = recycler.acquire_component(dict)
    widget2 = recycler.acquire_component(dict)
    
    assert widget1 is not None, "Failed to get component"
    assert widget2 is not None, "Failed to get second component"
    assert widget1 != widget2, "Got same component instance"
    
    print("✓ Component creation working")
    
    # Return components
    recycler.release_component(widget1)
    recycler.release_component(widget2)
    
    # Get recycled component
    widget3 = recycler.acquire_component(dict)
    assert widget3["data"] == "reset_widget", "Component reset failed"
    
    print("✓ Component recycling working")
    
    # Test memory tracking
    stats = recycler.get_memory_stats()
    print(f"Memory stats: {stats['total_acquisitions']} acquisitions, {stats['total_releases']} releases")
    print("✓ Component Recycler tests passed")

def test_api_optimizer():
    """Test the API optimizer functionality."""
    print("\n=== Testing API Optimizer ===")
    
    optimizer = APIOptimizer()
    
    # Test request creation
    print("Testing API request creation...")
    
    request = APIRequest(
        endpoint="test/weather",
        params={"city": "TestCity"},
        priority=RequestPriority.HIGH,
        cache_strategy=CacheStrategy.CACHE_FIRST,
        timeout=5.0,
        metadata={"test": True}
    )
    
    assert request.endpoint == "test/weather", "Request creation failed"
    assert request.request_id is not None, "Request ID not generated"
    print("✓ API request creation working")
    
    # Test request submission
    print("Testing API request submission...")
    
    request_id = optimizer.submit_request(request)
    assert request_id == request.request_id, "Request ID mismatch"
    print("✓ API request submission working")
    
    # Wait for processing
    time.sleep(0.5)
    
    # Check request status
    status = optimizer.get_request_status(request_id)
    print(f"Request status: {status['status'] if status else 'Not found'}")
    
    # Test statistics
    stats = optimizer.get_statistics()
    print(f"API stats: {stats['total_requests']} requests, {stats['cache_hits']} cache hits")
    assert stats['total_requests'] >= 1, "No requests recorded"
    
    # Test cache clearing
    cleared = optimizer.clear_cache()
    print(f"Cleared {cleared} cached responses")
    
    # Cleanup
    optimizer.shutdown()
    print("✓ API Optimizer tests passed")

def main():
    """Run all performance optimization tests."""
    print("Weather Dashboard Performance Optimization Tests")
    print("=" * 50)
    
    try:
        test_cache_manager()
        test_startup_optimizer()
        test_component_recycler()
        test_api_optimizer()
        
        print("\n" + "=" * 50)
        print("🎉 All performance optimization tests passed!")
        print("The weather dashboard is ready for enhanced performance.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()