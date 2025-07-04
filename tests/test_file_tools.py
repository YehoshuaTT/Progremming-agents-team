import unittest
from tools.file_tools import read_file, write_file
import os

class TestFileTools(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_file.txt"
        with open(self.test_file, "w") as f:
            f.write("Hello, world!")

    def tearDown(self):
        os.remove(self.test_file)

    def test_read_file(self):
        content = read_file(self.test_file)
        self.assertEqual(content, "Hello, world!")

    def test_write_file(self):
        new_content = "This is new content."
        write_file(self.test_file, new_content)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, new_content)

if __name__ == '__main__':
    unittest.main()
