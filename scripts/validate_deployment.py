#!/usr/bin/env python3
"""
Deployment validation script for Core-System
Validates that all services are running and accessible
"""
import requests
import time
import sys
import os
from datetime import datetime, timezone

def check_service(name, url, timeout=10):
    """Check if a service is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: {e}")
        return False

def validate_api_endpoints():
    """Validate all API endpoints"""
    base_url = "http://localhost:8000"
    endpoints = [
        ("Root", f"{base_url}/"),
        ("Health", f"{base_url}/health"),
        ("Stats", f"{base_url}/stats"),
        ("OpenAPI Docs", f"{base_url}/docs")
    ]
    
    results = []
    for name, url in endpoints:
        results.append(check_service(name, url))
    
    return all(results)

def validate_external_services():
    """Validate external services"""
    services = [
        ("Adminer", "http://localhost:8082"),
        ("MinIO Console", "http://localhost:9001")
    ]
    
    results = []
    for name, url in services:
        results.append(check_service(name, url))
    
    return all(results)

def test_sync_endpoint():
    """Test sync endpoint with dummy data"""
    try:
        import uuid
        
        payload = {
            "documents": [],
            "qa_entries": [],
            "batch_ts": datetime.now(timezone.utc).isoformat() + "Z"
        }
        
        # Test without token (should fail)
        response = requests.post("http://localhost:8000/sync/import", json=payload)
        if response.status_code == 422:
            print("✅ Sync endpoint: Authentication required (as expected)")
            return True
        else:
            print(f"❌ Sync endpoint: Unexpected response {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Sync endpoint test failed: {e}")
        return False

def main():
    print("🚀 Core-System Deployment Validation")
    print("=" * 50)
    
    # Wait a moment for services to start
    print("⏳ Waiting for services to start...")
    time.sleep(5)
    
    all_good = True
    
    print("\n📡 Validating API Endpoints:")
    if not validate_api_endpoints():
        all_good = False
    
    print("\n🌐 Validating External Services:")
    if not validate_external_services():
        all_good = False
    
    print("\n🔒 Testing Security:")
    if not test_sync_endpoint():
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All validations passed! Core-System is ready.")
        print("\n📋 Access URLs:")
        print("  • API: http://localhost:8000")
        print("  • API Docs: http://localhost:8000/docs")
        print("  • Health: http://localhost:8000/health")
        print("  • Stats: http://localhost:8000/stats")
        print("  • Adminer: http://localhost:8082")
        print("  • MinIO: http://localhost:9001")
        sys.exit(0)
    else:
        print("❌ Some validations failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
