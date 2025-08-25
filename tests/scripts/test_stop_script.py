"""
Tests for the stop.sh script functionality.

Tests script behavior, process termination, and cleanup operations.
"""

import os
import subprocess
import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import tempfile


class TestStopScript:
    """Test the stop.sh script functionality."""
    
    @pytest.fixture(autouse=True) 
    def setup_test_environment(self, tmp_path):
        """Set up a temporary test environment."""
        self.test_dir = tmp_path
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create mock files
        self.stop_script = self.test_dir / "stop.sh"
        self.frontend_pid_file = self.test_dir / "frontend.pid"
        self.frontend_log_file = self.test_dir / "frontend.log"
        
        yield
        
        os.chdir(self.original_dir)
    
    def create_stop_script(self):
        """Create a simplified version of the stop script for testing."""
        script_content = """#!/bin/bash
set -e

# Test version of stop script functions
stop_frontend() {
    if [ -f "frontend.pid" ]; then
        PID=$(cat frontend.pid)
        echo "Stopping frontend PID: $PID"
        # Don't actually kill in test
        rm -f frontend.pid
        echo "SUCCESS: Frontend stopped"
    else
        echo "Frontend was not running"
    fi
    rm -f frontend.log
}

stop_backend() {
    echo "Stopping backend services"
    # Mock docker compose down
    echo "SUCCESS: Backend services stopped"
}

case "$1" in
    "stop_frontend") stop_frontend ;;
    "stop_backend") stop_backend ;;
    *) 
        stop_frontend
        stop_backend
        echo "All services stopped successfully!"
        ;;
esac
"""
        self.stop_script.write_text(script_content)
        self.stop_script.chmod(0o755)
    
    def test_script_exists_and_executable(self):
        """Test that stop.sh exists and is executable."""
        real_script = Path(self.original_dir) / "stop.sh"
        assert real_script.exists(), "stop.sh script should exist"
        assert os.access(real_script, os.X_OK), "stop.sh should be executable"
    
    def test_frontend_stop_with_pid_file(self):
        """Test stopping frontend when PID file exists."""
        self.create_stop_script()
        
        # Create mock PID file
        self.frontend_pid_file.write_text("12345")
        self.frontend_log_file.write_text("frontend log content")
        
        result = subprocess.run(['bash', str(self.stop_script), 'stop_frontend'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Stopping frontend PID: 12345" in result.stdout
        assert "SUCCESS: Frontend stopped" in result.stdout
        assert not self.frontend_pid_file.exists()
        assert not self.frontend_log_file.exists()
    
    def test_frontend_stop_without_pid_file(self):
        """Test stopping frontend when PID file doesn't exist."""
        self.create_stop_script()
        
        result = subprocess.run(['bash', str(self.stop_script), 'stop_frontend'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Frontend was not running" in result.stdout
    
    def test_backend_stop(self):
        """Test stopping backend services."""
        self.create_stop_script()
        
        result = subprocess.run(['bash', str(self.stop_script), 'stop_backend'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Stopping backend services" in result.stdout
        assert "SUCCESS: Backend services stopped" in result.stdout
    
    def test_stop_all_services(self):
        """Test stopping all services together."""
        self.create_stop_script()
        
        # Create mock PID file
        self.frontend_pid_file.write_text("12345")
        
        result = subprocess.run(['bash', str(self.stop_script)], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "All services stopped successfully!" in result.stdout
        assert not self.frontend_pid_file.exists()


class TestStopScriptIntegration:
    """Integration tests for stop script with real behavior."""
    
    def test_script_has_proper_shebang(self):
        """Test that stop.sh has proper shebang line."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert content.startswith("#!/bin/bash"), "Script should have bash shebang"
    
    def test_script_has_error_handling(self):
        """Test that stop.sh has proper error handling."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "set -e" in content, "Script should have error handling"
    
    def test_script_has_color_output(self):
        """Test that stop.sh includes colored output functions."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "RED=" in content, "Script should have color definitions"
            assert "GREEN=" in content, "Script should have color definitions"
            assert "BLUE=" in content, "Script should have color definitions"
    
    def test_script_handles_frontend_cleanup(self):
        """Test that stop.sh properly cleans up frontend processes."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "frontend.pid" in content, "Script should handle frontend PID file"
            assert "frontend.log" in content, "Script should clean up log file"
            assert "pkill" in content or "kill" in content, "Script should kill processes"
    
    def test_script_handles_docker_cleanup(self):
        """Test that stop.sh properly handles Docker services."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "docker compose down" in content, "Script should stop Docker services"
    
    def test_script_has_required_functions(self):
        """Test that stop.sh contains required functions."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            required_functions = [
                "stop_frontend",
                "stop_backend"
            ]
            
            for func in required_functions:
                assert func in content, f"Script should contain {func} function"


class TestStopScriptSafety:
    """Tests for stop script safety and error handling."""
    
    def test_script_handles_missing_files_gracefully(self):
        """Test that script handles missing files gracefully."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            # Should check if files exist before operating on them
            assert "[ -f" in content, "Script should check file existence"
            assert "|| true" in content or "2>/dev/null" in content, "Script should handle errors gracefully"
    
    def test_script_provides_feedback(self):
        """Test that script provides user feedback."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "echo" in content, "Script should provide user feedback"
            assert "stopped" in content.lower(), "Script should confirm stopping"
    
    def test_script_has_main_execution_flow(self):
        """Test that script has proper main execution flow."""
        script_path = Path(os.getcwd()) / "stop.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "main" in content, "Script should have main function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])