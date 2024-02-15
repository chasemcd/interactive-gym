import dataclasses


@dataclasses.dataclass
class InputModes:
    # NOTE(chase): composite actions not available with single_keystroke
    SingleKeystroke = "single_keystroke"
    PressedKeys = "pressed_keys"
