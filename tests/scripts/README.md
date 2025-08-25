# Script Tests

This directory contains tests for the management and startup scripts.

## Test Files

- `test_start_script.py` - Tests for the startup script functionality
- `test_stop_script.py` - Tests for the stop script functionality  
- `test_restart_script.py` - Tests for the restart script functionality
- `test_logs_script.py` - Tests for the logs viewer script
- `test_health_script.py` - Tests for the health check script

## Running Tests

Run all script tests:
```bash
python -m pytest tests/scripts/ -v
```

Run specific script test:
```bash
python -m pytest tests/scripts/test_start_script.py -v
```

## Test Coverage

These tests verify:
- Script execution and argument parsing
- Error handling and validation
- Service integration and health checks
- Log output and status reporting
- Process management and cleanup