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

    def __init__(self, scene_id: str, experiment_config: dict):
        super().__init__(scene_id, experiment_config)
        self.scene_header: str = ""
        self.scene_subheader: str = ""
        self.self_body: str = ""

    def display(
        self,
        scene_header: str = NotProvided,
        scene_subheader: str = NotProvided,
        scene_body: str = NotProvided,
        scene_body_filepath: str = NotProvided,
    ) -> StaticScene:
        """Set the HTML file to be displayed in the scene.

        Args:
            filepath (str): The path to the HTML file to display in the scene.
            html_text (str): The HTML text to display in the scene.

        Returns:
            StaticScene: The StaticScene object.

        """
        if scene_body_filepath is not NotProvided:
            assert (
                scene_body is NotProvided
            ), "Cannot set both filepath and html_body."

            with open(scene_body_filepath, "r", encoding="utf-8") as f:
                self.scene_body = f.read()

        if scene_body is not NotProvided:
            assert (
                scene_body_filepath is NotProvided
            ), "Cannot set both filepath and html_body."
            self.scene_body = scene_body

        if scene_header is not NotProvided:
            self.scene_header = scene_header

        if scene_subheader is not NotProvided:
            self.scene_subheader = scene_subheader

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

    def __init__(self, scene_id: str, experiment_config: dict):
        super().__init__(scene_id, experiment_config)


class EndScene(StaticScene):
    """
    The EndScene is a special Scene that marks the end of the Stager sequence.

    If a redirect URL is provided, a button will appear to participants that will redirect them when
    clicked. Optionally, their subject_id can be appended to the URL (useful in cases where you
    are forwarding them to personalized surveys, etc.)
    """

    def __init__(self, scene_id: str, experiment_config: dict):
        super().__init__(scene_id, experiment_config)
        self.url: str | None = None
        self.append_subject_id: bool = False

    def redirect(
        self, url: str = NotProvided, append_subject_id: bool = NotProvided
    ) -> EndScene:
        if url is not NotProvided:
            self.url = url

        if append_subject_id is not NotProvided:
            self.append_subject_id = append_subject_id

        return self


class OptionBoxes(StaticScene):
    def __init__(
        self, scene_id: str, experiment_config: dict, options: list[str]
    ):
        super().__init__(scene_id, experiment_config)

        self.scene_body = self._create_html_option_boxes(options)

    def _create_html_option_boxes(self, options: list[str]) -> str:
        """
        Given a list of N options, creates HTML code to display a horizontal line of N boxes,
        each with a unique color. Each box is labeled by a string in the options list.
        When a user clicks a box, it becomes highlighted.
        The advance button is only enabled when a box is clicked.
        """
        colors = [
            "#FF6F61",
            "#6B5B95",
            "#88B04B",
            "#F7CAC9",
            "#92A8D1",
            "#955251",
            "#B565A7",
            "#009B77",
        ]  # Example colors
        html = '<div id="option-boxes-container" style="display: flex; justify-content: space-around; gap: 10px;">\n'

        for i, option in enumerate(options):
            color = colors[
                i % len(colors)
            ]  # Cycle through colors if there are more options than colors
            html += f"""
            <div id="option-{i}" class="option-box" style="
                background-color: {color};
                padding: 20px;
                cursor: pointer;
                border-radius: 10px;
                border: 2px solid transparent;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                text-align: center;
                transition: transform 0.2s ease, box-shadow 0.2s ease;">
                <span style="font-size: 16px; color: white;">{option}</span>
            </div>
            """

        html += "</div>\n"
        html += """
        <script>
        $("#advanceButton").attr("disabled", true);
        $("#advanceButton").show();

        document.querySelectorAll('.option-box').forEach(function(box) {
            box.addEventListener('click', function() {
                // Reset all boxes
                document.querySelectorAll('.option-box').forEach(function(b) {
                    b.style.border = '2px solid transparent';
                    b.style.transform = 'scale(1)';
                    b.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
                });

                // Highlight the clicked box
                box.style.border = '2px solid black';
                box.style.transform = 'scale(1.05)';
                box.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)';

                // Enable the advance button
                document.getElementById('advanceButton').disabled = false;
            });
        });

        </script>
        """

        return html


class OptionBoxesWithTextBox(StaticScene):
    def __init__(
        self,
        scene_id: str,
        experiment_config: dict,
        options: list[str],
        text_box_header: str,  # TODO(chase): Move this to .display()
    ):
        super().__init__(scene_id, experiment_config)

        self.scene_body = self._create_html_option_boxes(
            options, text_box_header
        )

    def _create_html_option_boxes(
        self, options: list[str], text_box_header: str
    ) -> str:
        """
        Given a list of N options, creates HTML code to display a horizontal line of N boxes,
        each with a unique color. Each box is labeled by a string in the options list.
        When a user clicks a box, it becomes highlighted.
        The advance button is only enabled when a box is clicked.
        """
        colors = [
            "#FF6F61",
            "#6B5B95",
            "#88B04B",
            "#F7CAC9",
            "#92A8D1",
            "#955251",
            "#B565A7",
            "#009B77",
        ]  # Example colors
        html = '<div id="option-boxes-container" style="display: flex; justify-content: space-around; gap: 10px;">\n'

        for i, option in enumerate(options):
            color = colors[
                i % len(colors)
            ]  # Cycle through colors if there are more options than colors
            html += f"""
            <div id="option-{i}" class="option-box" style="
                background-color: {color};
                padding: 20px;
                cursor: pointer;
                border-radius: 10px;
                border: 2px solid transparent;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                text-align: center;
                transition: transform 0.2s ease, box-shadow 0.2s ease;">
                <span style="font-size: 16px; color: white;">{option}</span>
            </div>
            """

        html += "</div>\n"
        html += "</div>\n"

        # Add text box
        html += f"""
        <div style="margin-top: 20px; text-align: center;">
            <h3>{text_box_header}</h3>
            <textarea id="user-input" rows="4" cols="50" style="width: 100%; max-width: 500px;"></textarea>
        </div>
        """

        html += """
        <script>
        $("#advanceButton").attr("disabled", true);
        $("#advanceButton").show();

        function checkInputs() {
            var boxSelected = document.querySelector('.option-box[style*="border: 2px solid black"]') !== null;
            var textEntered = document.getElementById('user-input').value.trim() !== '';
            document.getElementById('advanceButton').disabled = !(boxSelected && textEntered);
        }

        document.querySelectorAll('.option-box').forEach(function(box) {
            box.addEventListener('click', function() {
                // Reset all boxes
                document.querySelectorAll('.option-box').forEach(function(b) {
                    b.style.border = '2px solid transparent';
                    b.style.transform = 'scale(1)';
                    b.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
                });

                // Highlight the clicked box
                box.style.border = '2px solid black';
                box.style.transform = 'scale(1.05)';
                box.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)';

                // Enable the advance button
                document.getElementById('advanceButton').disabled = false;

                checkInputs();
            });
        });

        document.getElementById('user-input').addEventListener('input', checkInputs);
        </script>
        """

        return html
