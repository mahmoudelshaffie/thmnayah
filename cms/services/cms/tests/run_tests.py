#!/usr/bin/env python3
"""
Test runner script for CMS category management integration tests

This script provides convenient commands for running different types of tests
with appropriate configurations and reporting.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, description: str = None) -> int:
    """
    Run a command and return the exit code.
    
    Args:
        cmd: Command list to execute
        description: Optional description to print
        
    Returns:
        Exit code from command
    """
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running command: {e}")
        return 1


def run_integration_tests():
    """Run integration tests for category API endpoints."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "--durations=10",
        "-m", "integration"
    ]
    return run_command(cmd, "Integration Tests")


def run_category_api_tests():
    """Run specific category API tests."""
    cmd = [
        "python", "-m", "pytest", 
        "tests/integration/test_categories_api.py",
        "-v",
        "--tb=long",
        "--durations=10"
    ]
    return run_command(cmd, "Category API Tests")


def run_all_tests():
    """Run all tests with coverage."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v", 
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--durations=10"
    ]
    return run_command(cmd, "All Tests with Coverage")


def run_fast_tests():
    """Run only fast tests (excluding slow/performance tests)."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "-m", "not slow and not performance",
        "--durations=10"
    ]
    return run_command(cmd, "Fast Tests Only")


def run_performance_tests():
    """Run performance tests."""
    os.environ["RUN_PERFORMANCE_TESTS"] = "1"
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "-m", "performance",
        "--durations=0"
    ]
    return run_command(cmd, "Performance Tests")


def run_validation_tests():
    """Run validation-specific tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "-m", "validation",
        "--tb=short"
    ]
    return run_command(cmd, "Validation Tests")


def run_multilingual_tests():
    """Run multilingual functionality tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "-m", "multilingual",
        "--tb=short"
    ]
    return run_command(cmd, "Multilingual Tests")


def run_with_debug():
    """Run tests with debug output."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_categories_api.py",
        "-v", "-s",
        "--tb=long",
        "--log-cli-level=DEBUG",
        "--capture=no"
    ]
    return run_command(cmd, "Debug Mode Tests")


def check_test_environment():
    """Check if test environment is properly set up."""
    print("Checking test environment...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("ERROR: Python 3.8 or higher required")
        return False
    
    # Check required packages
    required_packages = [
        "pytest", "pytest-asyncio", "httpx", "sqlalchemy", "pydantic", "fastapi"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")
    
    if missing_packages:
        print(f"\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    # Check database
    try:
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///./test_check.db")
        engine.connect()
        os.remove("./test_check.db")
        print("✓ Database connection test passed")
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False
    
    print("\n✓ Test environment is ready!")
    return True


def clean_test_artifacts():
    """Clean up test artifacts and temporary files."""
    print("Cleaning test artifacts...")
    
    artifacts_to_clean = [
        "test.db",
        "htmlcov/",
        "coverage.xml",
        ".coverage",
        "tests/test_run.log",
        ".pytest_cache/",
        "__pycache__/",
        "*.pyc"
    ]
    
    for artifact in artifacts_to_clean:
        if os.path.exists(artifact):
            if os.path.isfile(artifact):
                os.remove(artifact)
                print(f"Removed file: {artifact}")
            elif os.path.isdir(artifact):
                import shutil
                shutil.rmtree(artifact)
                print(f"Removed directory: {artifact}")
    
    # Clean __pycache__ directories recursively
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_path = os.path.join(root, dir_name)
                import shutil
                shutil.rmtree(cache_path)
                print(f"Removed cache: {cache_path}")
    
    print("✓ Cleanup completed")


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Test runner for CMS category management system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py --integration    # Run integration tests
  python tests/run_tests.py --category-api   # Run category API tests
  python tests/run_tests.py --all           # Run all tests with coverage
  python tests/run_tests.py --fast          # Run fast tests only
  python tests/run_tests.py --performance   # Run performance tests
  python tests/run_tests.py --check         # Check test environment
  python tests/run_tests.py --clean         # Clean test artifacts
        """
    )
    
    # Test execution options
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run integration tests"
    )
    parser.add_argument(
        "--category-api", 
        action="store_true", 
        help="Run category API tests specifically"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all tests with coverage report"
    )
    parser.add_argument(
        "--fast", 
        action="store_true", 
        help="Run fast tests only (exclude slow/performance tests)"
    )
    parser.add_argument(
        "--performance", 
        action="store_true", 
        help="Run performance tests"
    )
    parser.add_argument(
        "--validation", 
        action="store_true", 
        help="Run validation tests"
    )
    parser.add_argument(
        "--multilingual", 
        action="store_true", 
        help="Run multilingual tests"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Run tests in debug mode with verbose output"
    )
    
    # Utility options
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check if test environment is properly configured"
    )
    parser.add_argument(
        "--clean", 
        action="store_true", 
        help="Clean test artifacts and temporary files"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return 0
    
    exit_code = 0
    
    try:
        if args.check:
            if not check_test_environment():
                return 1
                
        if args.clean:
            clean_test_artifacts()
            
        if args.integration:
            exit_code = run_integration_tests()
            
        elif args.category_api:
            exit_code = run_category_api_tests()
            
        elif args.all:
            exit_code = run_all_tests()
            
        elif args.fast:
            exit_code = run_fast_tests()
            
        elif args.performance:
            exit_code = run_performance_tests()
            
        elif args.validation:
            exit_code = run_validation_tests()
            
        elif args.multilingual:
            exit_code = run_multilingual_tests()
            
        elif args.debug:
            exit_code = run_with_debug()
    
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted")
        return 1
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())