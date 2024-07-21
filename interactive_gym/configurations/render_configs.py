from __future__ import annotations

import dataclasses
import typing


@dataclasses.dataclass
class Animation:
    key: str
    sprite_sheet_key: str
    frames: list[int]
    frameRate: int = None  # speed of animation
    repeat: int = -1  # -1 repeats infinitely
    hideOnComplete: bool = False
    object_type = "animation"

    def as_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)
