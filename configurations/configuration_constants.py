import dataclasses


@dataclasses.dataclass
class InputModes:
    SingleKeystroke = "single_keystroke"
    PressedKeys = "pressed_keys"
