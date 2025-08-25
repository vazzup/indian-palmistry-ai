"""
Tests for the start.sh script functionality.

Tests script behavior, Docker integration, health checks, and service startup.
"""

import os
import subprocess
import time
import pytest
import shutil
from unittest.mock import patch, Mock, call
from pathlib import Path
import tempfile
import json


class TestStartScript:
    """Test the start.sh script functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up a temporary test environment."""
        self.test_dir = tmp_path
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create mock script files
        self.start_script = self.test_dir / "start.sh"
        self.env_example = self.test_dir / ".env.example"
        self.frontend_dir = self.test_dir / "frontend"
        self.frontend_dir.mkdir()
        
        # Create mock .env.example
        self.env_example.write_text("""
# Example environment variables
DATABASE_URL=sqlite+aiosqlite:///./data/dev.db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-api-key-here
""")
        
        # Create mock package.json
        (self.frontend_dir / "package.json").write_text('{"name": "frontend", "scripts": {"dev": "next dev"}}')
        (self.frontend_dir / "node_modules").mkdir()
        
        yield
        
        os.chdir(self.original_dir)
    
    def create_start_script(self):
        """Create a simplified version of the start script for testing."""
        script_content = """#!/bin/bash
set -e

# Test version of start script functions
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "ERROR: Docker not found"
        exit 1
    fi
    echo "SUCCESS: Docker is running"
}

check_node() {
    if ! command -v node >/dev/null 2>&1; then
        echo "ERROR: Node.js not found" 
        exit 1
    fi
    echo "SUCCESS: Node.js is installed"
}

check_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "SUCCESS: Environment configuration ready"
        else
            echo "ERROR: .env.example not found"
            exit 1
        fi
    fi
}

case "$1" in
    "check_docker") check_docker ;;
    "check_node") check_node ;;
    "check_env") check_env ;;
    *) echo "Test script" ;;
esac
"""
        self.start_script.write_text(script_content)
        self.start_script.chmod(0o755)
    
    def test_script_exists_and_executable(self):
        """Test that start.sh exists and is executable."""
        real_script = Path(self.original_dir) / "start.sh"
        assert real_script.exists(), "start.sh script should exist"
        assert os.access(real_script, os.X_OK), "start.sh should be executable"
    
    def test_docker_check_success(self):
        """Test successful Docker availability check."""
        self.create_start_script()
        
        with patch('subprocess.run') as mock_run:
            # Mock successful docker command
            mock_run.return_value = Mock(returncode=0)
            
            result = subprocess.run(['bash', str(self.start_script), 'check_docker'], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "SUCCESS: Docker is running" in result.stdout
    
    def test_docker_check_failure(self):
        """Test Docker availability check failure."""
        self.create_start_script()
        
        with patch.dict(os.environ, {}, clear=True):
            # Remove docker from PATH
            with patch.dict(os.environ, {'PATH': ''}):
                result = subprocess.run(['bash', str(self.start_script), 'check_docker'], 
                                      capture_output=True, text=True)
                
                assert result.returncode == 1
                assert "ERROR: Docker not found" in result.stdout
    
    def test_node_check_success(self):
        """Test successful Node.js availability check."""
        self.create_start_script()
        
        result = subprocess.run(['bash', str(self.start_script), 'check_node'], 
                              capture_output=True, text=True)
        
        # Should succeed if Node.js is available on system
        if shutil.which('node'):
            assert result.returncode == 0
            assert "SUCCESS: Node.js is installed" in result.stdout
        else:
            assert result.returncode == 1
            assert "ERROR: Node.js not found" in result.stdout
    
    def test_env_file_creation(self):
        """Test .env file creation from .env.example."""
        self.create_start_script()
        
        # Ensure .env doesn't exist initially
        env_file = self.test_dir / ".env"
        if env_file.exists():
            env_file.unlink()
        
        result = subprocess.run(['bash', str(self.start_script), 'check_env'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "SUCCESS: Environment configuration ready" in result.stdout
        assert env_file.exists()
        
        # Verify .env content matches .env.example
        assert env_file.read_text() == self.env_example.read_text()
    
    def test_env_file_already_exists(self):
        """Test behavior when .env file already exists."""
        self.create_start_script()
        
        # Create existing .env file with different content
        env_file = self.test_dir / ".env"
        env_file.write_text("EXISTING_VAR=test")
        
        result = subprocess.run(['bash', str(self.start_script), 'check_env'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        # Should not overwrite existing file
        assert env_file.read_text() == "EXISTING_VAR=test"
    
    def test_missing_env_example(self):
        """Test error handling when .env.example is missing."""
        self.create_start_script()
        
        # Remove .env.example
        self.env_example.unlink()
        env_file = self.test_dir / ".env"
        if env_file.exists():
            env_file.unlink()
        
        result = subprocess.run(['bash', str(self.start_script), 'check_env'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "ERROR: .env.example not found" in result.stdout


class TestStartScriptIntegration:
    """Integration tests for start script with real services."""
    
    def test_script_has_proper_shebang(self):
        """Test that start.sh has proper shebang line."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert content.startswith("#!/bin/bash"), "Script should have bash shebang"
    
    def test_script_has_error_handling(self):
        """Test that start.sh has proper error handling."""
        script_path = Path(os.getcwd()) / "start.sh" 
        if script_path.exists():
            content = script_path.read_text()
            assert "set -e" in content, "Script should have error handling"
    
    def test_script_has_color_output(self):
        """Test that start.sh includes colored output functions."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "RED=" in content, "Script should have color definitions"
            assert "GREEN=" in content, "Script should have color definitions" 
            assert "BLUE=" in content, "Script should have color definitions"
            assert "print_status" in content, "Script should have status functions"
    
    def test_script_has_all_required_functions(self):
        """Test that start.sh contains all required functions."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            required_functions = [
                "check_docker",
                "check_node", 
                "check_env",
                "start_backend",
                "setup_database", 
                "start_frontend",
                "show_status"
            ]
            
            for func in required_functions:
                assert func in content, f"Script should contain {func} function"
    
    def test_script_handles_cleanup(self):
        """Test that start.sh has proper cleanup handling."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "cleanup" in content, "Script should have cleanup function"
            assert "trap" in content, "Script should set up signal traps"
    
    def test_script_validates_services(self):
        """Test that start.sh validates service health."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "curl" in content, "Script should use curl for health checks"
            assert "localhost:8000" in content, "Script should check API health"
            assert "healthz" in content, "Script should check health endpoint"


class TestStartScriptConfiguration:
    """Tests for start script configuration and parameters."""
    
    def test_script_uses_correct_ports(self):
        """Test that script references correct service ports.""" 
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "8000" in content, "Script should reference API port 8000"
            assert "3000" in content, "Script should reference frontend port 3000"
    
    def test_script_has_docker_compose_commands(self):
        """Test that script includes Docker Compose commands."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "docker compose" in content, "Script should use docker compose"
            assert "up -d" in content, "Script should start services in detached mode"
    
    def test_script_includes_database_migration(self):
        """Test that script includes database migration step."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "alembic" in content, "Script should run database migrations"
            assert "upgrade" in content, "Script should upgrade database"
    
    def test_script_manages_frontend_process(self):
        """Test that script properly manages frontend process."""
        script_path = Path(os.getcwd()) / "start.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "npm run dev" in content, "Script should start frontend dev server"
            assert "frontend.pid" in content, "Script should manage frontend PID"
            assert "frontend.log" in content, "Script should log frontend output"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])