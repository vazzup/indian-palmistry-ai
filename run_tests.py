#!/usr/bin/env python3
"""
Test runner for the Indian Palmistry AI project.

This script provides a simple way to run different categories of tests
and provides a summary of test coverage and results.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n🧪 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run test suite."""
    print("🚀 Indian Palmistry AI - Test Suite")
    print("====================================")
    
    # Test categories to run
    test_categories = [
        {
            "name": "Unit Tests (Services)",
            "command": "python -m pytest tests/test_services/ -v --tb=short -x",
            "description": "Testing core business logic services"
        },
        {
            "name": "Integration Tests (API Endpoints)",
            "command": "python -m pytest tests/test_api/ -v --tb=short -x",
            "description": "Testing REST API endpoints"
        },
        {
            "name": "Background Task Tests",
            "command": "python -m pytest tests/test_tasks/ -v --tb=short -x",
            "description": "Testing Celery background tasks"
        },
        {
            "name": "End-to-End Workflow Tests",
            "command": "python -m pytest tests/test_integration/ -v --tb=short -x",
            "description": "Testing complete user workflows"
        }
    ]
    
    results = []
    
    for category in test_categories:
        success = run_command(category["command"], category["name"])
        results.append((category["name"], success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:<35} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} categories")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All test categories passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test categories failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())