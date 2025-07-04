import unittest
import os
import json
from tools.task_tools import create_new_task, update_task_status, TASKS_DIR

class TestTaskTools(unittest.TestCase):

    def setUp(self):
        # Create a dummy task for testing
        self.task_id = create_new_task("Test Task", "This is a test task.")

    def tearDown(self):
        # Clean up the dummy task directory
        task_dir = os.path.join(TASKS_DIR, self.task_id)
        for file in os.listdir(task_dir):
            os.remove(os.path.join(task_dir, file))
        os.rmdir(task_dir)

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
