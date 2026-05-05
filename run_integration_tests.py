#!/usr/bin/env python3
"""
TAZARA Integration Test Runner

Run with: python run_integration_tests.py [options]

Options:
  -v, --verbose  Increase verbosity
  -k EXPRESSION  Only run tests that match the given substring expression
  -x, --exitfirst  Exit instantly on first error or failed test
"""
import sys
import pytest

def main():
    """Run integration tests with pytest"""
    # Default arguments
    args = [
        "tests/integration/",
        "-v",  # Verbose output
        "--tb=short",  # Shorter traceback format
        "-x",  # Stop on first failure
        "-W", "ignore::DeprecationWarning"  # Ignore deprecation warnings
    ]
    
    # Add any command line arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    # Run pytest with the configured arguments
    return pytest.main(args)

if __name__ == "__main__":
    sys.exit(main())
