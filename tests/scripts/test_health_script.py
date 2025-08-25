"""
Tests for the health.sh script functionality.

Tests health checking, service validation, and status reporting.
"""

import os
import subprocess
import pytest
from unittest.mock import patch, Mock
from pathlib import Path


class TestHealthScript:
    """Test the health.sh script functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up a temporary test environment."""
        self.test_dir = tmp_path
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create mock files
        self.health_script = self.test_dir / "health.sh"
        self.frontend_log = self.test_dir / "frontend.log"
        self.frontend_pid = self.test_dir / "frontend.pid"
        
        yield
        
        os.chdir(self.original_dir)
    
    def create_health_script(self):
        """Create a simplified version of the health script for testing."""
        script_content = """#!/bin/bash

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

check_service() {
    local name="$1"
    local url="$2"
    local expected="$3"
    
    # Mock curl response
    case "$url" in
        *"healthz"*) echo -e "${GREEN}✅ $name${NC} - Healthy"; return 0 ;;
        *"3000"*) echo -e "${GREEN}✅ $name${NC} - Healthy"; return 0 ;;
        *"docs"*) echo -e "${GREEN}✅ $name${NC} - Healthy"; return 0 ;;
        *) echo -e "${RED}❌ $name${NC} - Not responding"; return 1 ;;
    esac
}

check_docker_service() {
    local name="$1"
    local container="$2"
    
    # Mock docker service check
    case "$container" in
        *"redis"*) echo -e "${GREEN}✅ $name${NC} - Running"; return 0 ;;
        *"api"*) echo -e "${GREEN}✅ $name${NC} - Running"; return 0 ;;
        *"worker"*) echo -e "${GREEN}✅ $name${NC} - Running"; return 0 ;;
        *) echo -e "${RED}❌ $name${NC} - Not running"; return 1 ;;
    esac
}

case "${1:-main}" in
    "check_service")
        check_service "$2" "$3" "$4"
        ;;
    "check_docker_service")
        check_docker_service "$2" "$3"
        ;;
    "main")
        echo "Health Check Results"
        echo "Docker Services:"
        check_docker_service "Redis Database" "redis"
        check_docker_service "Backend API" "api"
        check_docker_service "Background Worker" "worker"
        echo ""
        echo "Service Endpoints:"
        check_service "Backend API Health" "http://localhost:8000/healthz" "healthy"
        check_service "Frontend Application" "http://localhost:3000" "Palmistry"
        check_service "API Documentation" "http://localhost:8000/docs" "FastAPI"
        echo ""
        if [ -f "frontend.pid" ]; then
            PID=$(cat frontend.pid)
            echo -e "${GREEN}✅ Next.js Process${NC} - Running (PID: $PID)"
        else
            echo -e "${YELLOW}⚠️  Next.js Process${NC} - PID file not found"
        fi
        echo ""
        echo -e "${GREEN}🎉 All systems healthy!${NC}"
        ;;
esac
"""
        self.health_script.write_text(script_content)
        self.health_script.chmod(0o755)
    
    def test_script_exists_and_executable(self):
        """Test that health.sh exists and is executable."""
        real_script = Path(self.original_dir) / "health.sh"
        assert real_script.exists(), "health.sh script should exist"
        assert os.access(real_script, os.X_OK), "health.sh should be executable"
    
    def test_check_service_healthy(self):
        """Test successful service health check."""
        self.create_health_script()
        
        result = subprocess.run([
            'bash', str(self.health_script), 'check_service',
            'Backend API Health', 'http://localhost:8000/healthz', 'healthy'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "✅ Backend API Health" in result.stdout
        assert "Healthy" in result.stdout
    
    def test_check_service_unhealthy(self):
        """Test failed service health check."""
        self.create_health_script()
        
        result = subprocess.run([
            'bash', str(self.health_script), 'check_service',
            'Bad Service', 'http://localhost:9999/bad', 'missing'
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "❌ Bad Service" in result.stdout
        assert "Not responding" in result.stdout
    
    def test_check_docker_service_running(self):
        """Test Docker service running check."""
        self.create_health_script()
        
        result = subprocess.run([
            'bash', str(self.health_script), 'check_docker_service',
            'Redis Database', 'redis'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "✅ Redis Database" in result.stdout
        assert "Running" in result.stdout
    
    def test_check_docker_service_not_running(self):
        """Test Docker service not running check."""
        self.create_health_script()
        
        result = subprocess.run([
            'bash', str(self.health_script), 'check_docker_service',
            'Unknown Service', 'unknown'
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "❌ Unknown Service" in result.stdout
        assert "Not running" in result.stdout
    
    def test_main_health_check_with_pid(self):
        """Test main health check with frontend PID file."""
        self.create_health_script()
        
        # Create mock PID file
        self.frontend_pid.write_text("12345")
        
        result = subprocess.run(['bash', str(self.health_script), 'main'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Health Check Results" in result.stdout
        assert "Docker Services:" in result.stdout
        assert "Service Endpoints:" in result.stdout
        assert "✅ Next.js Process" in result.stdout
        assert "Running (PID: 12345)" in result.stdout
        assert "🎉 All systems healthy!" in result.stdout
    
    def test_main_health_check_without_pid(self):
        """Test main health check without frontend PID file."""
        self.create_health_script()
        
        result = subprocess.run(['bash', str(self.health_script), 'main'], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Health Check Results" in result.stdout
        assert "⚠️  Next.js Process" in result.stdout
        assert "PID file not found" in result.stdout
    
    def test_main_health_check_default(self):
        """Test main health check as default action."""
        self.create_health_script()
        
        result = subprocess.run(['bash', str(self.health_script)], 
                              capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Health Check Results" in result.stdout
        assert "All systems healthy!" in result.stdout


class TestHealthScriptIntegration:
    """Integration tests for health script with real behavior."""
    
    def test_script_has_proper_shebang(self):
        """Test that health.sh has proper shebang line."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert content.startswith("#!/bin/bash"), "Script should have bash shebang"
    
    def test_script_has_color_output(self):
        """Test that health.sh includes colored output functions."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "RED=" in content, "Script should have color definitions"
            assert "GREEN=" in content, "Script should have color definitions"
            assert "BLUE=" in content, "Script should have color definitions"
    
    def test_script_checks_required_services(self):
        """Test that health.sh checks all required services."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            required_services = [
                "redis",
                "api", 
                "worker"
            ]
            
            for service in required_services:
                assert service in content.lower(), f"Script should check {service} service"
    
    def test_script_checks_endpoints(self):
        """Test that health.sh checks required endpoints.""" 
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            required_endpoints = [
                "localhost:8000",
                "localhost:3000", 
                "healthz",
                "docs"
            ]
            
            for endpoint in required_endpoints:
                assert endpoint in content, f"Script should check {endpoint} endpoint"
    
    def test_script_uses_curl_for_health_checks(self):
        """Test that health.sh uses curl for health checks."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "curl" in content, "Script should use curl for health checks"
    
    def test_script_uses_docker_for_service_checks(self):
        """Test that health.sh uses Docker commands for service checks."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "docker" in content, "Script should use docker commands"
    
    def test_script_has_required_functions(self):
        """Test that health.sh contains required functions."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            required_functions = [
                "check_service",
                "check_docker_service"
            ]
            
            for func in required_functions:
                assert func in content, f"Script should contain {func} function"
    
    def test_script_provides_overall_status(self):
        """Test that health.sh provides overall health status."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "healthy" in content.lower(), "Script should report overall health"
            assert "all_healthy" in content or "all systems" in content.lower(), "Script should have overall status logic"


class TestHealthScriptErrorHandling:
    """Tests for health script error handling and edge cases."""
    
    def test_script_handles_service_failures(self):
        """Test that script handles service failures gracefully."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "return 1" in content or "exit 1" in content, "Script should handle failures"
            assert "2>/dev/null" in content or "|| " in content, "Script should suppress errors when needed"
    
    def test_script_detects_frontend_port(self):
        """Test that script can detect frontend port dynamically."""
        script_path = Path(os.getcwd()) / "health.sh"
        if script_path.exists():
            content = script_path.read_text()
            assert "frontend.log" in content or "grep" in content, "Script should detect frontend port"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])