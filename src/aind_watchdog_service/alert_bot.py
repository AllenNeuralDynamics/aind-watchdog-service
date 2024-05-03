"""Module with Alert Bot for notifications on MS Teams"""

from typing import Optional

import requests


class AlertBot:
    """Class to handle sending alerts and messages in MS Teams."""

    def __init__(self, url: str):
        """
        AlertBot constructor

        Parameters
        ----------
        url : str
          The url to send the message to
        """
        self.url = url

    @staticmethod
    def _create_body_text(message: str, extra_text: Optional[str]) -> dict:
        """
        Parse strings into appropriate format to send to ms teams channel.
        Check here:
          https://learn.microsoft.com/en-us/microsoftteams/platform/
          task-modules-and-cards/cards/cards-reference#adaptive-card
        Parameters
        ----------
        message : str
          The main message content
        extra_text : Optional[str]
          Additional text to send in card body

        Returns
        -------
        dict

        """
        body: list = [
            {
                "type": "TextBlock",
                "size": "Medium",
                "weight": "Bolder",
                "text": message,
            }
        ]
        if extra_text is not None:
            body.append({"type": "TextBlock", "text": extra_text})
        contents = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": body,
                        "$schema": (
                            "http://adaptivecards.io/schemas/" "adaptive-card.json"
                        ),
                        "version": "1.0",
                    },
                }
            ],
        }
        return contents

    def send_message(
        self, message: str, extra_text: Optional[str] = None
    ) -> Optional[requests.Response]:
        """
        Sends a message  via requests.post

        Parameters
        ----------
        message : str
          The main message content
        extra_text : Optional[str]
          Additional text to send in card body

        Returns
        -------
        Optional[requests.Response]
          If the url is None, only print and return None. Otherwise, post
          message to url and return the response.

        """
        contents = self._create_body_text(message, extra_text)
        response = requests.post(self.url, json=contents)
        return response
