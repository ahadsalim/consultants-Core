#!/usr/bin/env python3
"""
Health check script for Docker container
"""
import sys
import requests
import os

def main():
    try:
        # Check if the API is responding
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            
            # Check if all services are healthy
            if health_data.get("status") == "ok":
                print("✅ All services healthy")
                sys.exit(0)
            elif health_data.get("status") == "degraded":
                print("⚠️ Services degraded:")
                if not health_data.get("db"):
                    print("  - Database connection failed")
                if not health_data.get("minio"):
                    print("  - MinIO connection failed")
                sys.exit(1)
            else:
                print("❌ Unknown health status")
                sys.exit(1)
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
