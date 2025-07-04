import unittest
from unittest.mock import patch
from tools.git_tools import git_create_branch, git_add_and_commit

class TestGitTools(unittest.TestCase):

    @patch('subprocess.run')
    def test_git_create_branch(self, mock_run):
        git_create_branch("test-branch")
        mock_run.assert_called_with(["git", "checkout", "-b", "test-branch"], check=True)

    @patch('subprocess.run')
    def test_git_add_and_commit(self, mock_run):
        git_add_and_commit("Test commit")
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_any_call(["git", "add", "."], check=True)
        mock_run.assert_any_call(["git", "commit", "-m", "Test commit"], check=True)

if __name__ == '__main__':
    unittest.main()
