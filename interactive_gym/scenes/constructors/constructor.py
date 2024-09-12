class Constructor:
    """_summary_

    A constructor is a utility class that generates pre-structures HTML code for a specific scene,
    e.g., adding a text box, buttons, etc.
    """

    def __init__(
        self,
        object_name_prefix: str,
        require_to_advance: bool = True,
        *args,
        **kwargs
    ):
        self.object_name_prefix = object_name_prefix
        self.require_to_advance = require_to_advance

    def build() -> str:
        """Generate the HTML code to be added to a specific scene. This must be implemented for each Constructor class.

        :raises NotImplementedError: Must implement this method for each Constructor class.
        :return: Returns the HTML code to add to a scene.
        :rtype: str
        """
        raise NotImplementedError
