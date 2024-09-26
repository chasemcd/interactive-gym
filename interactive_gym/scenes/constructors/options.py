from interactive_gym.scenes.constructors import constructor


class OptionBoxes(constructor.Constructor):

    def __init__(
        self,
        object_name_prefix: str,
        options: list[str],
        require_to_advance: bool = True,
    ):
        super().__init__(object_name_prefix, require_to_advance)
        self.options = options

    def _create_html_option_boxes(self) -> str:
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
        ]
        html = f'<div id="{self.object_name_prefix}-option-boxes-container" style="display: flex; justify-content: space-around; gap: 10px;">\n'

        for i, option in enumerate(self.options):
            color = colors[
                i % len(colors)
            ]  # Cycle through colors if there are more options than colors
            html += f"""
            <div id="{self.object_name_prefix}-option-{i}" class="option-box" style="
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

        html += f"""
        <script>
        $("#advanceButton").attr("disabled", true);
        $("#advanceButton").show();

        document.querySelectorAll('#{self.object_name_prefix}-option-boxes-container .option-box').forEach(function(box) {{
            box.addEventListener('click', function() {{
                // Reset all boxes
                document.querySelectorAll('#{self.object_name_prefix}-option-boxes-container .option-box').forEach(function(b) {{
                    b.style.border = '2px solid transparent';
                    b.style.transform = 'scale(1)';
                    b.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
                }});

                // Highlight the clicked box
                box.style.border = '2px solid black';
                box.style.transform = 'scale(1.05)';
                box.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)';

                // Enable the advance button
                document.getElementById('advanceButton').disabled = false;
            }});
        }});

        </script>
        """

        return html

    def build(self) -> str:
        return self._create_html_option_boxes(self.options)
