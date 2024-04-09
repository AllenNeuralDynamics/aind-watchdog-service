"""Example test template."""

import unittest
import yaml
from aind_watchdog_service import config
class TestConfig(unittest.TestCase):
    """Example Test Class"""

    @classmethod
    def setUp(cls) -> None:
        cls.path_to_config = "resources/rig_config.yml"


    def test_config(self):
        """Example of how to test the truth of a statement."""
        with open(self.path_to_config) as yam:
            data = yaml.safe_load(yam)
        watchdog_config = config.WatchConfig(**data)
        self.assertEqual(watchdog_config.model_dump, data)


if __name__ == "__main__":
    unittest.main()
