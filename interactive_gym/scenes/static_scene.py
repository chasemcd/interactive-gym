from __future__ import annotations


from typing import Any

from flask_socketio import SocketIO

from interactive_gym.scenes import scene
from interactive_gym.scenes.utils import NotProvided


class StaticScene(scene.Scene):
    """StaticScene is a Scene that represents a static web page with text/images displayed.

    HTML Scenes will all have a "Continue" button on the bottom of the page. This button will be immediately
    available unless a canContinue element is provided in the HTML file. If the canContinue element included provided,
    the button will only be enabled once the element evaluates to true, e.g.,:

        let canContinue = document.getElemendById("canContinue");
        if (canContinue == undefined) {
                 $("#continueButton").attr("disabled", false);
            } else {
                canContinue.onchange = function() {
                    if (canContinue.value == "true") {
                        $("#continueButton").attr("disabled", false);
                    } else {
                        $("#continueButton").attr("disabled", true);
                    }
                }
            }
        }

    """

    def __init__(self, scene_name: str, **kwargs):
        self.scene_name: str | None = scene_name
        self.html_body: str = ""

    def html(
        self, filepath: str = NotProvided, html_body: str = NotProvided
    ) -> StaticScene:
        """Set the HTML file to be displayed in the scene.

        Args:
            filepath (str): The path to the HTML file to display in the scene.
            html_text (str): The HTML text to display in the scene.

        Returns:
            StaticScene: The StaticScene object.

        """
        if filepath is not NotProvided:
            assert (
                self.html_body is None and html_body is NotProvided
            ), "Cannot set both filepath and html_body."

            with open(filepath, "r", encoding="utf-8") as f:
                self.html_body = f.read()

        if html_body is not NotProvided:
            assert (
                filepath is NotProvided
            ), "Cannot set both filepath and html_body."
            self.html_body = html_body

        return self

    def process_page_elements(
        self, page_elements: dict[str, Any]
    ) -> dict[str, Any]:
        """

        TODO(chase): Use

            function emitAllElements() {
                const elements = document.querySelectorAll('input, textarea, select');  // Add more selectors as needed
                const data = {};

                elements.forEach(element => {
                    if (element.name) {
                        data[element.name] = element.value;
                    }
                });

                socket.emit('page_elements', data);
            }

        to emit all of the elements on the page to the server, then pass it to this function as needed.


        Process the elements of the page when the continue button is pressed.

        We'll get a dictionary of:
            getElementsByTagName(*)

        Args:
            data (Any): All of the elements on the page.

        Returns:
            StaticScene: The StaticScene object.

        """
        pass


class StartScene(StaticScene):
    """
    The StartScene is a special Scene that marks the beginning of the Stager sequence.
    """

    def start_page(
        self, header_text: str = NotProvided, body_text: str = NotProvided
    ) -> StartScene:
        """Set the text for the start page.

        Args:
            header_text (str): The text to display in the header.
            body_text (str): The text to display in the body.

        Returns:
            StartScene: The StartScene object.

        """
        if header_text is not NotProvided:
            self.header_text = header_text

        if body_text is not NotProvided:
            self.body_text = body_text

        return self

    def activate(self, sio: SocketIO):
        return super().activate(sio)


class EndScene(StaticScene):
    """
    The EndScene is a special Scene that marks the end of the Stager sequence.
    """

    def end_page(
        self, header_text: str = NotProvided, body_text: str = NotProvided
    ) -> StartScene:
        """Set the text for the end page.

        Args:
            header_text (str): The text to display in the header.
            body_text (str): The text to display in the body.

        Returns:
            StartScene: The StartScene object.

        """
        if header_text is not NotProvided:
            self.header_text = header_text

        if body_text is not NotProvided:
            self.body_text = body_text

        return self
