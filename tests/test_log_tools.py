import unittest
import os
import json
import tempfile
from unittest.mock import patch
from tests.base_test import BaseTestCase

class TestLogTools(BaseTestCase):

    def setUp(self):
        # Call parent setUp
        super().setUp()
        # Patch EXECUTION_LOG to a unique temp file for this test
        self.temp_log = tempfile.NamedTemporaryFile(delete=False)
        self.temp_log.close()
        self.patcher = patch('tools.log_tools.EXECUTION_LOG', self.temp_log.name)
        self.patcher.start()
        from tools.log_tools import record_log  # Import after patching
        self.record_log = record_log
        # Track the execution log for cleanup
        self.add_test_file(self.temp_log.name)

    def tearDown(self):
        self.patcher.stop()
        super().tearDown()

    def test_record_log(self):
        self.record_log("TEST-001", "test_event", {"data": "test_data"})
        self.assertTrue(os.path.exists(self.temp_log.name))
        import time
        for _ in range(10):
            with open(self.temp_log.name, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        log_entry = json.loads(line)
                        self.assertEqual(log_entry["task_id"], "TEST-001")
                        self.assertEqual(log_entry["event"], "test_event")
                        return
            time.sleep(0.02)
        self.fail("Log file is empty or contains only blank lines after waiting!")

if __name__ == '__main__':
    unittest.main()
