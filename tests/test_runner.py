import unittest
from unittest.mock import patch, mock_open, MagicMock
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil
import json

# Add src to the path to allow importing prp_runner
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from prp_runner import main

class TestPrpRunner(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for test files."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    @patch('subprocess.Popen')
    def test_run_success_without_system_prompt(self, mock_popen):
        """Test successful execution of a PRP file without a system prompt."""
        # Arrange
        runners_manifest = self.test_dir / "runners.json"
        runners_manifest.write_text(json.dumps([
            {
                "runner_name": "claude-cli",
                "command_template": ["claude", "-p", "{prompt}"]
            }
        ]))

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("Test content")

        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "claude-cli"],
            manifest_path=runners_manifest
        )

        # Assert
        self.assertEqual(result, 0)
        mock_popen.assert_called_once_with(["claude", "-p", "Test content"], stderr=subprocess.PIPE, text=True)

    @patch('subprocess.Popen')
    def test_run_with_system_prompt(self, mock_popen):
        """Test successful execution with a system prompt."""
        # Arrange
        runners_manifest = self.test_dir / "runners.json"
        runners_manifest.write_text(json.dumps([
            {
                "runner_name": "claude-cli",
                "command_template": ["claude", "-p", "{prompt}"],
                "system_prompt_template": "System: {prp_content}"
            }
        ]))

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("PRP content")

        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "claude-cli"],
            manifest_path=runners_manifest
        )

        # Assert
        self.assertEqual(result, 0)
        mock_popen.assert_called_once_with(["claude", "-p", "System: PRP content"], stderr=subprocess.PIPE, text=True)

    def test_run_missing_runner(self):
        """Test that the program exits if the specified runner is not found."""
        # Arrange
        runners_manifest = self.test_dir / "runners.json"
        runners_manifest.write_text(json.dumps([
            {
                "runner_name": "claude-cli",
                "command_template": ["claude", "-p", "{prompt}"]
            }
        ]))

        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("Test content")

        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "non-existent-runner"],
            manifest_path=runners_manifest
        )

        # Assert
        self.assertEqual(result, 1)

    def test_run_missing_prp_file(self):
        """Test that the program exits if the PRP file does not exist."""
        # Arrange
        runners_manifest = self.test_dir / "runners.json"
        runners_manifest.write_text(json.dumps([
            {
                "runner_name": "any-runner",
                "command_template": ["echo", "{prompt}"]
            }
        ]))

        # Act
        result = main.run_from_args(
            ["--prp", "non_existent_file.md", "--runner", "any-runner"],
            manifest_path=runners_manifest
        )

        # Assert
        self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
