import unittest
from unittest.mock import patch
from tools.execution_tools import execute_shell_command

class TestExecutionTools(unittest.TestCase):

    @patch('subprocess.run')
    def test_execute_shell_command(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        result = execute_shell_command("echo 'Success'", agent_id="test_agent")
        self.assertEqual(result['success'], True)
        self.assertEqual(result['output'], "Success")

    def test_execute_shell_command_blocked(self):
        # Test that blocked commands return security error
        result = execute_shell_command("dangerous_command", agent_id="test_agent")
        self.assertEqual(result['success'], False)
        self.assertIn("Security violation", result['error'])

if __name__ == '__main__':
    unittest.main()
