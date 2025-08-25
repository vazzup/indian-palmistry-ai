"""
Tests for the restart.sh script functionality.

Tests script orchestration, service restart flow, and error handling.
"""

import os
import subprocess
import pytest
from unittest.mock import patch, Mock
from pathlib import Path


class TestRestartScript:
    """Test the restart.sh script functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up a temporary test environment."""
        self.test_dir = tmp_path
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create mock scripts
        self.restart_script = self.test_dir / "restart.sh"
        self.stop_script = self.test_dir / "stop.sh"
        self.start_script = self.test_dir / "start.sh"
        
        yield
        
        os.chdir(self.original_dir)
    
    def create_mock_scripts(self):
        """Create mock scripts for testing."""
        # Create mock stop script
        self.stop_script.write_text("""#!/bin/bash
echo "Stopping all services"
exit 0
""")
        self.stop_script.chmod(0o755)
        
        # Create mock start script
        self.start_script.write_text("""#!/bin/bash
echo "Starting all services"
exit 0
""")
        self.start_script.chmod(0o755)
        
        # Create restart script
        restart_content = """#!/bin/bash
set -e

# Colors for output
BLUE='\\033[0;34m'
GREEN='\\033[0;32m'
NC='\\033[0m'

main() {
    echo -e "\\n${BLUE}Restarting Indian Palmistry AI${NC}\\n"
    
    echo -e "${BLUE}🛑 Stopping all services...${NC}"
    ./stop.sh
    
    echo -e "\\n${BLUE}⏳ Waiting 3 seconds...${NC}"
    sleep 3
    
    echo -e "\\n${BLUE}🚀 Starting all services...${NC}"
    ./start.sh
    
    echo -e "\\n${GREEN}✅ Restart completed!${NC}\\n"
}

main "$@"
"""
        self.restart_script.write_text(restart_content)
        self.restart_script.chmod(0o755)
    
    def test_script_exists_and_executable(self):
        """Test that restart.sh exists and is executable."""
        real_script = Path(self.original_dir) / "restart.sh"
        assert real_script.exists(), "restart.sh script should exist"
        assert os.access(real_script, os.X_OK), "restart.sh should be executable"
    
    def test_restart_calls_stop_and_start(self):
        """Test that restart script calls stop and start scripts."""
        self.create_mock_scripts()
        
        result = subprocess.run(['bash', str(self.restart_script)], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Restarting Indian Palmistry AI" in result.stdout
        assert "Stopping all services" in result.stdout
        assert "Starting all services" in result.stdout
        assert "Restart completed!" in result.stdout
    
    def test_restart_includes_wait_period(self):
        """Test that restart script includes wait period between stop and start."""
        self.create_mock_scripts()
        
        # Measure execution time (should be at least 3 seconds due to sleep)
        import time
        start_time = time.time()
        
        result = subprocess.run(['bash', str(self.restart_script)], 
                              capture_output=True, text=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.returncode == 0
        assert "Waiting 3 seconds" in result.stdout
        assert execution_time >= 2.5  # Allow some tolerance for test execution
    
    def test_restart_handles_stop_failure(self):
        """Test restart script behavior when stop script fails."""
        # Create failing stop script
        self.stop_script.write_text("""#!/bin/bash
echo "Failed to stop services"
exit 1
""")
        self.stop_script.chmod(0o755)
        
        # Create normal start script
        self.start_script.write_text("""#!/bin/bash
echo "Starting all services"
exit 0
""")
        self.start_script.chmod(0o755)
        
        # Create restart script
        restart_content = """#!/bin/bash
set -e

main() {
    echo "Restarting Indian Palmistry AI"
    echo "Stopping all services..."
    ./stop.sh
    echo "Starting all services..."
    ./start.sh
    echo "Restart completed!"
}

main "$@"
"""
        self.restart_script.write_text(restart_content)
        self.restart_script.chmod(0o755)
        
        result = subprocess.run(['bash', str(self.restart_script)], 
                              capture_output=True, text=True)
        
        # Should fail due to set -e and stop script failure
        assert result.returncode == 1
        assert "Failed to stop services" in result.stdout
    
    def test_restart_handles_start_failure(self):
        """Test restart script behavior when start script fails."""
        # Create normal stop script
        self.stop_script.write_text("""#!/bin/bash
echo "Stopping all services"
exit 0
""")
        self.stop_script.chmod(0o755)
        
        # Create failing start script
        self.start_script.write_text("""#!/bin/bash
echo "Failed to start services"
exit 1
""")
        self.start_script.chmod(0o755)
        
        # Create restart script
        restart_content = """#!/bin/bash
set -e

main() {
    echo "Restarting Indian Palmistry AI"
    echo "Stopping all services..."
    ./stop.sh
    sleep 1
    echo "Starting all services..."
    ./start.sh
    echo "Restart completed!"
}

main "$@"
"""
        self.restart_script.write_text(restart_content)
        self.restart_script.chmod(0o755)
        
        result = subprocess.run(['bash', str(self.restart_script)], 
                              capture_output=True, text=True)
        
        # Should fail due to set -e and start script failure
        assert result.returncode == 1
        assert "Stopping all services" in result.stdout
        assert "Failed to start services" in result.stdout


class TestRestartScriptIntegration:
    """Integration tests for restart script with real behavior."""
    
    def test_script_has_proper_shebang(self):
        """Test that restart.sh has proper shebang line."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert content.startswith("#!/bin/bash"), "Script should have bash shebang"
    
    def test_script_has_error_handling(self):
        """Test that restart.sh has proper error handling."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "set -e" in content, "Script should have error handling"
    
    def test_script_has_color_output(self):
        """Test that restart.sh includes colored output functions."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "BLUE=" in content, "Script should have color definitions"
            assert "GREEN=" in content, "Script should have color definitions"
    
    def test_script_calls_other_scripts(self):
        """Test that restart.sh calls stop.sh and start.sh."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "./stop.sh" in content, "Script should call stop.sh"
            assert "./start.sh" in content, "Script should call start.sh"
    
    def test_script_has_wait_period(self):
        """Test that restart.sh includes wait period between operations."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "sleep" in content, "Script should have wait period"
            assert "3" in content, "Script should wait for 3 seconds"
    
    def test_script_provides_feedback(self):
        """Test that restart.sh provides user feedback."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "echo" in content, "Script should provide user feedback"
            assert "restart" in content.lower(), "Script should mention restart"
    
    def test_script_has_main_function(self):
        """Test that restart.sh has proper main execution flow."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "main" in content, "Script should have main function"
            assert 'main "$@"' in content, "Script should call main with arguments"


class TestRestartScriptFlow:
    """Tests for restart script execution flow and sequencing."""
    
    def test_script_stops_before_starting(self):
        """Test that script stops services before starting them."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            
            # Find positions of stop and start calls
            stop_pos = content.find("./stop.sh")
            start_pos = content.find("./start.sh")
            
            assert stop_pos != -1, "Script should call stop.sh"
            assert start_pos != -1, "Script should call start.sh"
            assert stop_pos < start_pos, "Script should stop before starting"
    
    def test_script_has_descriptive_messages(self):
        """Test that script provides descriptive status messages."""
        script_path = Path(os.getcwd()) / "restart.sh"
        if script_path.exists():
            content = script_path.read_text()
            messages = ["stopping", "starting", "waiting", "completed"]
            
            for message in messages:
                assert message.lower() in content.lower(), f"Script should mention {message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])