import unittest
import os
import json
from tools.log_tools import record_log, EXECUTION_LOG
from tests.base_test import BaseTestCase

class TestLogTools(BaseTestCase):

    def setUp(self):
        # Call parent setUp
        super().setUp()
        # Track the execution log for cleanup
        self.add_test_file(EXECUTION_LOG)

    def test_record_log(self):
        # Clear the log file first
        if os.path.exists(EXECUTION_LOG):
            os.remove(EXECUTION_LOG)
        
        record_log("TEST-001", "test_event", {"data": "test_data"})
        self.assertTrue(os.path.exists(EXECUTION_LOG))
        with open(EXECUTION_LOG, "r") as f:
            log_entry = json.loads(f.readline())
            self.assertEqual(log_entry["task_id"], "TEST-001")
            self.assertEqual(log_entry["event"], "test_event")

if __name__ == '__main__':
    unittest.main()
