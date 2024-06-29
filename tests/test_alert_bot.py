"""Testing Alerts: Alessio B"""

import unittest
from unittest import mock
from unittest.mock import MagicMock, call

from aind_watchdog_service.alert_bot import AlertBot


class TestAlertBot(unittest.TestCase):
    """Tests methods in AlertBot class"""

    @mock.patch("requests.post")
    def test_send_message(self, mocked_post: MagicMock) -> None:
        """
        Tests that the message is being sent correctly
        Parameters
        ----------
        mocked_post : MagicMock
          mock the request.post calls
        mock_print : MagicMock
          mock the print calls

        Returns
        -------
        None

        """
        alert_bot = AlertBot("testing_url.com")
        alert_bot.send_message(message="Test Message")
        contents0 = alert_bot._create_body_text("Test Message", None)
        mocked_post.assert_called_once_with("testing_url.com", json=contents0)
        alert_bot.send_message(message="Another Message", extra_text="With extra text")
        contents1 = alert_bot._create_body_text("Another Message", "With extra text")
        mocked_post.assert_has_calls(
            [
                call("testing_url.com", json=contents0),
                call("testing_url.com", json=contents1),
            ]
        )


if __name__ == "__main__":
    unittest.main()
