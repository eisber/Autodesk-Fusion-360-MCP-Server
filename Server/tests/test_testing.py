"""Tests for the testing tools module."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Mock the config before importing testing module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSaveTest:
    """Tests for save_test function."""

    @patch('src.tools.testing.requests.get')
    @patch('src.tools.testing.TEST_STORAGE_PATH')
    def test_save_test_success(self, mock_path, mock_get, tmp_path):
        """Test saving a test successfully."""
        mock_path.__str__ = lambda x: str(tmp_path)
        # Patch at module level
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            from src.tools.testing import save_test
            
            result = save_test(
                name="test_body_count",
                script="assert_body_count(1)",
                description="Verify one body exists"
            )
            
            assert result["success"] is True
            assert "test_body_count" in result["message"]
            assert os.path.exists(result["file_path"])
            
            # Verify file contents
            with open(result["file_path"], "r") as f:
                data = json.load(f)
            assert data["name"] == "test_body_count"
            assert data["script"] == "assert_body_count(1)"
            assert data["description"] == "Verify one body exists"

    @patch('src.tools.testing.requests.get')
    def test_save_test_invalid_name(self, mock_get, tmp_path):
        """Test saving a test with invalid name."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            from src.tools.testing import save_test
            
            result = save_test(name="", script="pass", description="")
            assert result["success"] is False
            assert "Invalid" in result["error"]


class TestLoadTests:
    """Tests for load_tests function."""

    @patch('src.tools.testing.requests.get')
    def test_load_tests_empty(self, mock_get, tmp_path):
        """Test loading tests when none exist."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            from src.tools.testing import load_tests
            
            result = load_tests()
            assert result["success"] is True
            assert result["tests"] == []
            assert result["test_count"] == 0

    @patch('src.tools.testing.requests.get')
    def test_load_tests_with_tests(self, mock_get, tmp_path):
        """Test loading tests when some exist."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            # Create test directory and file
            test_dir = tmp_path / "TestProject"
            test_dir.mkdir()
            test_file = test_dir / "my_test.json"
            test_file.write_text(json.dumps({
                "name": "my_test",
                "description": "A test",
                "script": "pass",
                "created_at": "2025-01-01T00:00:00"
            }))
            
            from src.tools.testing import load_tests
            
            result = load_tests()
            assert result["success"] is True
            assert result["test_count"] == 1
            assert result["tests"][0]["name"] == "my_test"


class TestRunTests:
    """Tests for run_tests function."""

    @patch('src.tools.testing.requests.get')
    def test_run_tests_single_not_found(self, mock_get, tmp_path):
        """Test running a non-existent test."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            from src.tools.testing import run_tests
            
            result = run_tests("nonexistent_test")
            assert result["success"] is False
            assert result["passed"] is False
            assert "not found" in result["error"]

    @patch('src.tools.testing.requests.get')
    @patch('src.tools.scripting.execute_fusion_script')
    def test_run_tests_single_success(self, mock_exec, mock_get, tmp_path):
        """Test running a single test successfully."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            # Create test file
            test_dir = tmp_path / "TestProject"
            test_dir.mkdir()
            test_file = test_dir / "my_test.json"
            test_file.write_text(json.dumps({
                "name": "my_test",
                "script": "result = 'ok'",
            }))
            
            # Mock script execution
            mock_exec.return_value = {
                "success": True,
                "return_value": "ok",
                "stdout": "",
                "model_state": {"body_count": 1}
            }
            
            from src.tools.testing import run_tests
            
            result = run_tests("my_test")
            assert result["success"] is True
            assert result["passed"] is True
            assert result["return_value"] == "ok"

    @patch('src.tools.testing.requests.get')
    def test_run_tests_all_empty(self, mock_get, tmp_path):
        """Test running all tests when none exist."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            from src.tools.testing import run_tests
            
            result = run_tests()
            assert result["success"] is True
            assert result["total"] == 0
            assert result["passed"] == 0
            assert result["failed"] == 0

    @patch('src.tools.testing.requests.get')
    @patch('src.tools.scripting.execute_fusion_script')
    def test_run_tests_all_mixed_results(self, mock_exec, mock_get, tmp_path):
        """Test running all tests with mixed pass/fail."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            # Create test files
            test_dir = tmp_path / "TestProject"
            test_dir.mkdir()
            
            (test_dir / "test_pass.json").write_text(json.dumps({
                "name": "test_pass",
                "script": "result = 'ok'",
            }))
            (test_dir / "test_fail.json").write_text(json.dumps({
                "name": "test_fail",
                "script": "assert False",
            }))
            
            # Mock script execution - alternate pass/fail
            def mock_execute(script):
                if "assert False" in script:
                    return {"success": False, "error": "AssertionError"}
                return {"success": True, "return_value": "ok"}
            
            mock_exec.side_effect = mock_execute
            
            from src.tools.testing import run_tests
            
            result = run_tests()
            assert result["total"] == 2
            assert result["passed"] == 1
            assert result["failed"] == 1
            assert result["success"] is False  # Not all passed


class TestSnapshots:
    """Tests for snapshot functions."""

    @patch('src.tools.testing.requests.get')
    def test_create_snapshot(self, mock_get, tmp_path):
        """Test creating a snapshot."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "design_name": "TestProject",
                    "body_count": 2,
                    "sketch_count": 1
                }
            )
            
            from src.tools.testing import create_snapshot
            
            result = create_snapshot("before_changes")
            assert result["success"] is True
            assert result["body_count"] == 2
            assert result["sketch_count"] == 1
            assert os.path.exists(result["file_path"])

    @patch('src.tools.testing.requests.get')
    def test_list_snapshots(self, mock_get, tmp_path):
        """Test listing snapshots."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            # Create snapshot directory and file
            snap_dir = tmp_path / "TestProject" / "snapshots"
            snap_dir.mkdir(parents=True)
            (snap_dir / "snap1.json").write_text(json.dumps({
                "name": "snap1",
                "created_at": "2025-01-01T00:00:00",
                "model_state": {"body_count": 1, "sketch_count": 0}
            }))
            
            from src.tools.testing import list_snapshots
            
            result = list_snapshots()
            assert result["success"] is True
            assert result["snapshot_count"] == 1
            assert result["snapshots"][0]["name"] == "snap1"

    @patch('src.tools.testing.requests.get')
    @patch('src.tools.testing.send_request')
    def test_restore_snapshot_already_at_state(self, mock_send, mock_get, tmp_path):
        """Test restoring when already at target state."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "design_name": "TestProject",
                    "body_count": 2,
                    "sketch_count": 1
                }
            )
            
            # Create snapshot
            snap_dir = tmp_path / "TestProject" / "snapshots"
            snap_dir.mkdir(parents=True)
            (snap_dir / "target.json").write_text(json.dumps({
                "name": "target",
                "model_state": {"body_count": 2, "sketch_count": 1}
            }))
            
            from src.tools.testing import restore_snapshot
            
            result = restore_snapshot("target")
            assert result["success"] is True
            assert result["undo_count"] == 0
            assert "already at" in result["message"]

    @patch('src.tools.testing.requests.get')
    def test_restore_snapshot_impossible(self, mock_get, tmp_path):
        """Test restoring when snapshot requires more bodies."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "design_name": "TestProject",
                    "body_count": 1,  # Current: 1 body
                    "sketch_count": 0
                }
            )
            
            # Create snapshot requiring more bodies
            snap_dir = tmp_path / "TestProject" / "snapshots"
            snap_dir.mkdir(parents=True)
            (snap_dir / "target.json").write_text(json.dumps({
                "name": "target",
                "model_state": {"body_count": 3, "sketch_count": 0}  # Target: 3 bodies
            }))
            
            from src.tools.testing import restore_snapshot
            
            result = restore_snapshot("target")
            assert result["success"] is False
            assert "Cannot restore" in result["error"]


class TestDeleteFunctions:
    """Tests for delete functions."""

    @patch('src.tools.testing.requests.get')
    def test_delete_test(self, mock_get, tmp_path):
        """Test deleting a test."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            # Create test file
            test_dir = tmp_path / "TestProject"
            test_dir.mkdir()
            test_file = test_dir / "to_delete.json"
            test_file.write_text("{}")
            
            from src.tools.testing import delete_test
            
            result = delete_test("to_delete")
            assert result["success"] is True
            assert not test_file.exists()

    @patch('src.tools.testing.requests.get')
    def test_delete_snapshot(self, mock_get, tmp_path):
        """Test deleting a snapshot."""
        with patch('src.tools.testing.TEST_STORAGE_PATH', str(tmp_path)):
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"design_name": "TestProject"}
            )
            
            # Create snapshot file
            snap_dir = tmp_path / "TestProject" / "snapshots"
            snap_dir.mkdir(parents=True)
            snap_file = snap_dir / "to_delete.json"
            snap_file.write_text("{}")
            
            from src.tools.testing import delete_snapshot
            
            result = delete_snapshot("to_delete")
            assert result["success"] is True
            assert not snap_file.exists()
