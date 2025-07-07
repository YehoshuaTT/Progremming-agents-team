import unittest
import os
import json
from tools.task_tools import create_new_task, update_task_status, TASKS_DIR
from tests.base_test import BaseTestCase

class TestTaskTools(BaseTestCase):

    def setUp(self):
        # Call parent setUp
        super().setUp()
        # Create a dummy task for testing
        self.task_id = create_new_task("Test Task", "This is a test task.")
        # Track the task directory for cleanup
        task_dir = os.path.join(TASKS_DIR, self.task_id)
        self.add_test_directory(task_dir)

    def test_create_new_task(self):
        self.assertTrue(os.path.exists(os.path.join(TASKS_DIR, self.task_id)))
        with open(os.path.join(TASKS_DIR, self.task_id, "task.json"), "r") as f:
            task_data = json.load(f)
            self.assertEqual(task_data["title"], "Test Task")

    def test_update_task_status(self):
        update_task_status(self.task_id, "IN_PROGRESS")
        with open(os.path.join(TASKS_DIR, self.task_id, "task.json"), "r") as f:
            task_data = json.load(f)
            self.assertEqual(task_data["status"], "IN_PROGRESS")

if __name__ == '__main__':
    unittest.main()
