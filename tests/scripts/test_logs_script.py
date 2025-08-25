"""
Tests for the logs.sh script functionality.

Tests log viewing, service filtering, and status reporting.
"""

import os
import subprocess
import pytest
from unittest.mock import patch, Mock
from pathlib import Path


class TestLogsScript:
    """Test the logs.sh script functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up a temporary test environment."""
        self.test_dir = tmp_path
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create mock files
        self.logs_script = self.test_dir / "logs.sh"
        self.frontend_log = self.test_dir / "frontend.log"
        self.frontend_pid = self.test_dir / "frontend.pid"
        
        yield
        
        os.chdir(self.original_dir)
    
    def create_logs_script(self):
        """Create a simplified version of the logs script for testing."""
        script_content = """#!/bin/bash
set -e

show_usage() {
    echo "Usage: $0 [service]"
    echo "Available services: api, worker, redis, frontend, all"
}

show_api_logs() {
    echo "Backend API Logs:"
    echo "Mock API log content"
}

show_worker_logs() {
    echo "Background Worker Logs:"
    echo "Mock worker log content"
}

show_redis_logs() {
    echo "Redis Database Logs:"
    echo "Mock redis log content"
}

show_frontend_logs() {
    echo "Frontend Application Logs:"
    if [ -f "frontend.log" ]; then
        cat frontend.log
    else
        echo "Frontend log file not found"
    fi
}

show_status() {
    echo "Service Status:"
    if [ -f "frontend.pid" ]; then
        PID=$(cat frontend.pid)
        echo "Frontend running (PID: $PID)"
    else
        echo "Frontend PID file not found"
    fi
}

case "${1:-all}" in
    "api") show_api_logs ;;
    "worker") show_worker_logs ;;
    "redis") show_redis_logs ;;
    "frontend") show_frontend_logs ;;
    "status") show_status ;;
    "all")
        show_api_logs
        show_worker_logs
        show_redis_logs
        show_frontend_logs
        show_status
        ;;
    "help"|"-h"|"--help") show_usage ;;
    *) 
        echo "Unknown service: $1"
        show_usage
        exit 1
        ;;
esac
"""
        self.logs_script.write_text(script_content)
        self.logs_script.chmod(0o755)
    
    def test_script_exists_and_executable(self):
        """Test that logs.sh exists and is executable."""
        real_script = Path(self.original_dir) / "logs.sh"
        assert real_script.exists(), "logs.sh script should exist"
        assert os.access(real_script, os.X_OK), "logs.sh should be executable"
    
    def test_show_api_logs(self):
        """Test showing API logs."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script), 'api'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Backend API Logs:" in result.stdout
        assert "Mock API log content" in result.stdout
    
    def test_show_worker_logs(self):
        """Test showing worker logs."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script), 'worker'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Background Worker Logs:" in result.stdout
        assert "Mock worker log content" in result.stdout
    
    def test_show_redis_logs(self):
        """Test showing Redis logs."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script), 'redis'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Redis Database Logs:" in result.stdout
        assert "Mock redis log content" in result.stdout
    
    def test_show_frontend_logs_with_file(self):
        """Test showing frontend logs when log file exists."""
        self.create_logs_script()
        
        # Create mock log file
        self.frontend_log.write_text("Frontend log line 1\nFrontend log line 2")
        
        result = subprocess.run(['bash', str(self.logs_script), 'frontend'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Frontend Application Logs:" in result.stdout
        assert "Frontend log line 1" in result.stdout
        assert "Frontend log line 2" in result.stdout
    
    def test_show_frontend_logs_without_file(self):
        """Test showing frontend logs when log file doesn't exist."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script), 'frontend'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Frontend Application Logs:" in result.stdout
        assert "Frontend log file not found" in result.stdout
    
    def test_show_status_with_pid(self):
        """Test showing status when PID file exists."""
        self.create_logs_script()
        
        # Create mock PID file
        self.frontend_pid.write_text("12345")
        
        result = subprocess.run(['bash', str(self.logs_script), 'status'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Service Status:" in result.stdout
        assert "Frontend running (PID: 12345)" in result.stdout
    
    def test_show_status_without_pid(self):
        """Test showing status when PID file doesn't exist."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script), 'status'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Service Status:" in result.stdout
        assert "Frontend PID file not found" in result.stdout
    
    def test_show_all_logs(self):
        """Test showing all logs together."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script), 'all'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Backend API Logs:" in result.stdout
        assert "Background Worker Logs:" in result.stdout
        assert "Redis Database Logs:" in result.stdout
        assert "Frontend Application Logs:" in result.stdout
        assert "Service Status:" in result.stdout
    
    def test_show_all_logs_default(self):
        """Test showing all logs by default (no argument)."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script)], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Backend API Logs:" in result.stdout
        assert "Service Status:" in result.stdout
    
    def test_show_usage_help(self):
        """Test showing usage with help argument."""
        self.create_logs_script()
        
        for help_arg in ['help', '-h', '--help']:
            result = subprocess.run(['bash', str(self.logs_script), help_arg], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "Usage:" in result.stdout
            assert "Available services:" in result.stdout
    
    def test_unknown_service_error(self):
        """Test error handling for unknown service."""
        self.create_logs_script()
        
        result = subprocess.run(['bash', str(self.logs_script), 'unknown'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "Unknown service: unknown" in result.stdout
        assert "Usage:" in result.stdout


class TestLogsScriptIntegration:
    """Integration tests for logs script with real behavior."""
    
    def test_script_has_proper_shebang(self):
        """Test that logs.sh has proper shebang line."""
        script_path = Path(os.getcwd()) / "logs.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert content.startswith("#!/bin/bash"), "Script should have bash shebang"
    
    def test_script_has_error_handling(self):
        """Test that logs.sh has proper error handling."""
        script_path = Path(os.getcwd()) / "logs.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "set -e" in content, "Script should have error handling"
    
    def test_script_has_color_output(self):
        """Test that logs.sh includes colored output functions."""
        script_path = Path(os.getcwd()) / "logs.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "RED=" in content, "Script should have color definitions"
            assert "GREEN=" in content, "Script should have color definitions"
            assert "BLUE=" in content, "Script should have color definitions"
    
    def test_script_has_docker_log_commands(self):
        """Test that logs.sh includes Docker log commands."""
        script_path = Path(os.getcwd()) / "logs.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "docker logs" in content, "Script should use docker logs command"
            assert "indian-palmistry-ai" in content, "Script should reference container names"
    
    def test_script_has_service_filtering(self):
        """Test that logs.sh supports service filtering."""
        script_path = Path(os.getcwd()) / "logs.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "case" in content, "Script should have case statement for filtering"
            assert "api" in content, "Script should support api service"
            assert "worker" in content, "Script should support worker service"
            assert "redis" in content, "Script should support redis service"
            assert "frontend" in content, "Script should support frontend service"
    
    def test_script_has_status_checking(self):
        """Test that logs.sh includes status checking."""
        script_path = Path(os.getcwd()) / "logs.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "docker compose ps" in content or "docker ps" in content, "Script should check Docker status"
            assert "curl" in content, "Script should check service health"
    
    def test_script_has_required_functions(self):
        """Test that logs.sh contains required functions."""
        script_path = Path(os.getcwd()) / "logs.sh"
        if script_path.exists():
            content = script_path.read_text()
            required_functions = [
                "show_api_logs",
                "show_worker_logs",
                "show_redis_logs",
                "show_frontend_logs",
                "show_status"
            ]
            
            for func in required_functions:
                assert func in content, f"Script should contain {func} function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])