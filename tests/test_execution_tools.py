import unittest
from unittest.mock import patch
from tools.execution_tools import execute_shell_command

class TestExecutionTools(unittest.TestCase):

    @patch('subprocess.run')
    def test_execute_shell_command(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        result = execute_shell_command("echo 'Success'")
        self.assertEqual(result, "Success")

    @patch('subprocess.run')
    def test_execute_shell_command_error(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error"
        result = execute_shell_command("error_command")
        self.assertEqual(result, "Error")

if __name__ == '__main__':
    unittest.main()
