#!/usr/bin/env python3
"""
Test Harness for Poker EV Trainer Backend

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --unit       # Run only unit tests
    python run_tests.py --api        # Run only API tests
    python run_tests.py --perf       # Run only performance tests
    python run_tests.py --coverage   # Run with coverage report
    python run_tests.py --verbose    # Run with verbose output
    python run_tests.py -k "cache"   # Run tests matching pattern
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def check_dependencies():
    """Check if test dependencies are installed."""
    required = ['pytest', 'pytest_asyncio', 'httpx']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print_error(f"Missing test dependencies: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements-dev.txt")
        return False
    
    return True


def run_tests(args):
    """Run pytest with the specified arguments."""
    # Base pytest command
    cmd = [sys.executable, '-m', 'pytest']
    
    # Add test directory
    test_dir = Path(__file__).parent / 'tests'
    
    # Filter by test type
    if args.unit:
        cmd.extend([str(test_dir / 'test_equity_cache.py')])
        print_info("Running unit tests only...")
    elif args.api:
        cmd.extend([str(test_dir / 'test_api_precompute.py')])
        print_info("Running API tests only...")
    elif args.perf:
        cmd.extend(['-k', 'Performance', str(test_dir)])
        print_info("Running performance tests only...")
    else:
        cmd.append(str(test_dir))
        print_info("Running all tests...")
    
    # Add pattern filter if specified
    if args.pattern:
        cmd.extend(['-k', args.pattern])
    
    # Add verbosity
    if args.verbose:
        cmd.append('-v')
    else:
        cmd.append('-v')  # Default to verbose
    
    # Add coverage if requested
    if args.coverage:
        try:
            import pytest_cov
            cmd.extend(['--cov=app', '--cov-report=html', '--cov-report=term'])
            print_info("Coverage reporting enabled...")
        except ImportError:
            print_error("pytest-cov not installed. Run: pip install pytest-cov")
            return 1
    
    # Add short traceback
    cmd.append('--tb=short')
    
    # Add color
    cmd.append('--color=yes')
    
    # Print command
    print_info(f"Command: {' '.join(cmd)}")
    print()
    
    # Run tests
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Test harness for Poker EV Trainer backend',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Test type filters
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--unit', action='store_true', 
                       help='Run only unit tests (equity cache)')
    group.add_argument('--api', action='store_true',
                       help='Run only API endpoint tests')
    group.add_argument('--perf', action='store_true',
                       help='Run only performance tests')
    
    # Other options
    parser.add_argument('-k', '--pattern', type=str,
                        help='Run tests matching pattern')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--coverage', action='store_true',
                        help='Generate coverage report')
    parser.add_argument('--check-deps', action='store_true',
                        help='Only check if dependencies are installed')
    
    args = parser.parse_args()
    
    print_header("Poker EV Trainer - Test Harness")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    if args.check_deps:
        print_success("All test dependencies installed!")
        return 0
    
    # Run tests
    exit_code = run_tests(args)
    
    # Print summary
    print()
    if exit_code == 0:
        print_success("All tests passed!")
    else:
        print_error(f"Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())

