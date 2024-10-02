class Constructor:
    """
    TODO(chase): Constructors are meant to modularize the HTML/JS code for specific static scenes,
        which can easily become unweildy if contained in a single class. These are under active
        development and are not funcational yet. We need to figure out the most general way to check
        the require_to_advance list and ensure, regarless of their element type, that the user
        has completed them before advancing.

    A constructor is a utility class that generates pre-structures HTML code for a specific scene,
    e.g., adding a text box, buttons, etc.
    """

    def __init__(
        self,
        object_name_prefix: str,
        require_to_advance: list[str] | None = None,
        *args,
        **kwargs
    ):
        self.require_to_advance = require_to_advance or []
        self.object_name_prefix = object_name_prefix

    def build() -> tuple[str, list[str]]:
        """Generate the HTML code to be added to a specific scene. This must be implemented for each Constructor class.

        :raises NotImplementedError: Must implement this method for each Constructor class.
        :return: Returns a tuple of the HTML code to add to a scene and the list of objects
            that must be checked in order to advance the scene.
        :rtype: tuple[str, list[str]]
        """
        raise NotImplementedError
