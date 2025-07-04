import unittest
from tools.file_tools import read_file, write_file
import os
import tempfile

class TestFileTools(unittest.TestCase):

    def setUp(self):
        # Create a temporary file in a safe location
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        with open(self.test_file, "w") as f:
            f.write("Hello, world!")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_read_file_blocked(self):
        # Test that non-sandbox files are blocked
        result = read_file(self.test_file, agent_id="test_agent")
        self.assertEqual(result['success'], False)
        self.assertIn("Security violation", result['error'])

    def test_write_file_blocked(self):
        # Test that non-sandbox files are blocked
        new_content = "This is new content."
        write_result = write_file(self.test_file, new_content, agent_id="test_agent")
        self.assertEqual(write_result['success'], False)
        self.assertIn("Security violation", write_result['error'])

if __name__ == '__main__':
    unittest.main()
