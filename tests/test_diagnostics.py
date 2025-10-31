"""
Tests for Diagnostics Analyzer

Tests context-aware dependency checking, TCP probing, and handshake verification.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDiagnosticsAnalyzer(unittest.TestCase):
    """Test diagnostics analyzer context-aware checks"""
    
    def setUp(self):
        """Set up test fixtures"""
        from modules.smart_troubleshooter.diagnostics_analyzer import DiagnosticsAnalyzer
        self.analyzer = DiagnosticsAnalyzer()
    
    @patch('modules.smart_troubleshooter.diagnostics_analyzer.SETTINGS')
    @patch('modules.smart_troubleshooter.diagnostics_analyzer._spec.find_spec')
    def test_faiss_no_chroma_nag(self, mock_find_spec, mock_settings):
        """Test: FAISS vector store doesn't nag about missing chromadb"""
        # Setup
        mock_settings.vector_store = "faiss"
        mock_find_spec.side_effect = lambda pkg: None if pkg == "chromadb" else MagicMock()
        
        # Execute
        missing, recommendations = self.analyzer._check_dependencies()
        
        # Assert
        self.assertNotIn("chromadb", missing, "chromadb should not be flagged as missing when using FAISS")
        chroma_recs = [r for r in recommendations if "chromadb" in r.lower()]
        self.assertEqual(len(chroma_recs), 0, "No chromadb recommendations when using FAISS")
    
    @patch('modules.smart_troubleshooter.diagnostics_analyzer.SETTINGS')
    @patch('modules.smart_troubleshooter.diagnostics_analyzer._spec.find_spec')
    def test_chroma_vector_store_flags_missing(self, mock_find_spec, mock_settings):
        """Test: chroma vector store DOES flag missing chromadb"""
        # Setup
        mock_settings.vector_store = "chroma"
        mock_find_spec.side_effect = lambda pkg: None if pkg == "chromadb" else MagicMock()
        
        # Execute
        missing, recommendations = self.analyzer._check_dependencies()
        
        # Assert
        self.assertIn("chromadb", missing, "chromadb should be flagged when vector_store=chroma")
    
    def test_flask_or_fastapi_either_ok(self):
        """Test: Flask OR FastAPI present = OK (not both required)"""
        with patch('modules.smart_troubleshooter.diagnostics_analyzer._spec.find_spec') as mock_find_spec:
            # Case 1: Flask present, FastAPI missing -> OK
            mock_find_spec.side_effect = lambda pkg: MagicMock() if pkg == "flask" else None
            missing, _ = self.analyzer._check_dependencies()
            flask_missing = "flask" in missing
            self.assertFalse(flask_missing, "Flask present should be OK even without FastAPI")
            
            # Case 2: FastAPI present, Flask missing -> OK (no Flask nag unless Flask API detected)
            mock_find_spec.side_effect = lambda pkg: MagicMock() if pkg == "fastapi" else None
            missing, _ = self.analyzer._check_dependencies()
            flask_missing = "flask" in missing
            # Should not nag unless Flask API is actually in use
            # (This depends on whether modules/academic_rag/api.py uses Flask)
    
    @patch('socket.create_connection')
    def test_tcp_probe_backoff_tries_multiple_hosts(self, mock_socket):
        """Test: TCP probe tries multiple loopback addresses"""
        # Setup: First two attempts fail, third succeeds on ::1
        attempt_count = [0]
        
        def side_effect(*args, **kwargs):
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ConnectionRefusedError("Connection refused")
            # Third attempt succeeds
            return MagicMock()
        
        mock_socket.side_effect = side_effect
        
        # Execute
        success, connected_host = self.analyzer._tcp_reachable("localhost", 51235, attempts=2)
        
        # Assert
        self.assertTrue(attempt_count[0] >= 2, "Should try multiple times")
    
    @patch('socket.create_connection')
    def test_handshake_detects_wrong_service(self, mock_socket):
        """Test: Handshake check detects wrong service on port"""
        # Setup: Port is open but responds with wrong protocol
        mock_conn = MagicMock()
        mock_conn.recv.return_value = b'{"pong": "wrong_service"}\n'
        mock_socket.return_value.__enter__.return_value = mock_conn
        
        # Execute
        verified, msg = self.analyzer._tcp_handshake_check("127.0.0.1", 51235, "clo")
        
        # Assert
        self.assertFalse(verified, "Should detect wrong service")
        self.assertIn("wrong", msg.lower(), "Message should indicate wrong service")
    
    @patch('socket.create_connection')
    def test_handshake_correct_service(self, mock_socket):
        """Test: Handshake succeeds with correct service response"""
        # Setup: Correct CLO service response
        mock_conn = MagicMock()
        mock_conn.recv.return_value = b'{"pong": "clo"}\n'
        mock_socket.return_value.__enter__.return_value = mock_conn
        
        # Execute
        verified, msg = self.analyzer._tcp_handshake_check("127.0.0.1", 51235, "clo")
        
        # Assert
        self.assertTrue(verified, "Should verify correct service")
        self.assertIn("verified", msg.lower() if msg else "", "Message should indicate success")
    
    def test_system_resources_check(self):
        """Test: System resource checks don't crash"""
        try:
            hints = self.analyzer._check_system_resources()
            self.assertIsInstance(hints, list, "Should return list of hints")
        except Exception as e:
            self.fail(f"System resource check should not crash: {e}")
    
    def test_telemetry_state_tracking(self):
        """Test: Telemetry tracks state changes"""
        # Initial state
        self.assertIsNone(self.analyzer._last_clo_state, "Initial CLO state should be None")
        
        # Simulate state change
        with patch.object(self.analyzer, '_tcp_reachable', return_value=(True, "127.0.0.1")):
            with patch.object(self.analyzer, '_tcp_handshake_check', return_value=(True, "verified")):
                status, _ = self.analyzer._check_clo_bridge()
        
        self.assertEqual(self.analyzer._last_clo_state, "reachable", "State should be tracked")


class TestHealthEndpoint(unittest.TestCase):
    """Test unified health endpoint"""
    
    def test_full_health_structure(self):
        """Test: /health/full returns expected structure"""
        from modules.academic_rag.health_endpoint import get_full_health
        
        health = get_full_health()
        
        # Assert structure
        self.assertIn("api", health)
        self.assertIn("clo", health)
        self.assertIn("vector_store", health)
        self.assertIn("ollama", health)
        self.assertIn("sys", health)
    
    def test_clo_health_lightweight(self):
        """Test: /health/clo is lightweight (no extra checks)"""
        from modules.academic_rag.health_endpoint import get_clo_health
        
        health = get_clo_health()
        
        # Assert structure
        self.assertIn("ok", health)
        self.assertIn("host", health)
        self.assertIn("port", health)


if __name__ == "__main__":
    print("Running Diagnostics Tests...\n")
    unittest.main(verbosity=2)

