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
        # Mock stdout and stderr to capture print statements
        self.patcher_stdout = patch('sys.stdout')
        self.patcher_stderr = patch('sys.stderr')
        self.mock_stdout = self.patcher_stdout.start()
        self.mock_stderr = self.patcher_stderr.start()

    def tearDown(self):
        """Clean up the temporary directory and mocks."""
        shutil.rmtree(self.test_dir)
        self.patcher_stdout.stop()
        self.patcher_stderr.stop()

    def _create_runner_manifest(self, data):
        """Helper to create a runners.json file."""
        runners_manifest = self.test_dir / "runners.json"
        runners_manifest.write_text(json.dumps(data))
        return runners_manifest

    @patch('subprocess.Popen')
    def test_run_success_without_system_prompt(self, mock_popen):
        """Test successful execution without a system prompt, checking cwd."""
        # Arrange
        manifest = self._create_runner_manifest([
            {"runner_name": "basic-cli", "command_template": ["echo", "{prompt}"]}
        ])
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ["Done."]
        mock_process.communicate.return_value = ("Done.", "")
        mock_popen.return_value = mock_process

        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("Test content")

        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "basic-cli"], manifest_path=manifest
        )

        # Assert
        self.assertEqual(result, 0)
        mock_popen.assert_called_once()
        # Check command
        self.assertEqual(mock_popen.call_args.args[0], ["echo", "Test content"])
        # Check that working directory is set correctly
        self.assertEqual(mock_popen.call_args.kwargs['cwd'], self.test_dir)

    @patch('subprocess.Popen')
    def test_run_with_system_prompt_and_working_dir(self, mock_popen):
        """Test successful execution with a system prompt and {working_dir} placeholder."""
        # Arrange
        manifest = self._create_runner_manifest([
            {
                "runner_name": "claude-cli",
                "command_template": ["claude", "-p", "{prompt}"],
                "system_prompt_template": "Dir: {working_dir} Plan: {prp_content}"
            }
        ])
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ["Output line 1", "Output line 2"]
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("PRP content")

        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "claude-cli"], manifest_path=manifest
        )

        # Assert
        self.assertEqual(result, 0)
        expected_prompt = f"Dir: {self.test_dir} Plan: PRP content"
        mock_popen.assert_called_once_with(
            ["claude", "-p", expected_prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.test_dir,
            bufsize=1,
            universal_newlines=True
        )

    def test_run_missing_runner(self):
        """Test that the program exits if the specified runner is not found."""
        # Arrange
        manifest = self._create_runner_manifest([
            {"runner_name": "claude-cli", "command_template": ["claude", "-p", "{prompt}"]}
        ])
        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("Test content")

        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "non-existent-runner"], manifest_path=manifest
        )

        # Assert
        self.assertEqual(result, 1)
        stderr_output = "".join(call.args[0] for call in self.mock_stderr.write.call_args_list)
        self.assertIn(f"Error: Runner 'non-existent-runner' not found in {manifest}.", stderr_output)

    @patch('subprocess.Popen')
    def test_run_command_not_found(self, mock_popen):
        """Test that the program exits if the command is not found."""
        # Arrange
        manifest = self._create_runner_manifest([
            {"runner_name": "missing-cmd", "command_template": ["missing-cmd", "{prompt}"]}
        ])
        mock_popen.side_effect = FileNotFoundError
        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("Test content")
        
        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "missing-cmd"], manifest_path=manifest
        )
        
        # Assert
        self.assertEqual(result, 1)
        stderr_output = "".join(call.args[0] for call in self.mock_stderr.write.call_args_list)
        self.assertIn("Error: Command 'missing-cmd' not found.", stderr_output)

    @patch('subprocess.Popen')
    def test_run_command_fails_with_non_zero_exit(self, mock_popen):
        """Test that the program handles a non-zero exit code from the runner."""
        # Arrange
        manifest = self._create_runner_manifest([
            {"runner_name": "failing-cmd", "command_template": ["failing-cmd", "{prompt}"]}
        ])

        mock_process = MagicMock()
        mock_process.returncode = 127
        mock_process.stdout = ["Starting..."]
        mock_process.communicate.return_value = ("", "Command failed with an error.")
        mock_popen.return_value = mock_process

        prp_file = self.test_dir / "test.prp"
        prp_file.write_text("Test content")

        # Act
        result = main.run_from_args(
            ["--prp", str(prp_file), "--runner", "failing-cmd"], manifest_path=manifest
        )

        # Assert
        self.assertEqual(result, 127)
        mock_popen.assert_called_once()

        # Check that the error was printed to stderr
        stderr_output = "".join(call.args[0] for call in self.mock_stderr.write.call_args_list)
        self.assertIn("--- Runner exited with code 127 ---", stderr_output)
        self.assertIn("Error output:\nCommand failed with an error.", stderr_output)

    @patch('sys.exit')
    def test_load_runners_invalid_json(self, mock_exit):
        """Test that the program exits if the runner manifest is malformed JSON."""
        # Arrange
        manifest = self.test_dir / "runners.json"
        manifest.write_text("this is not json")
        
        # Act
        main.load_runners(manifest)
        
        # Assert
        mock_exit.assert_called_once_with(1)
        stderr_output = "".join(call.args[0] for call in self.mock_stderr.write.call_args_list)
        self.assertIn(f"Error: Invalid format in {manifest}: Expecting value: line 1 column 1 (char 0)", stderr_output)

if __name__ == '__main__':
    unittest.main()
