
from dataclasses import dataclass
from typing import Literal

from pygame import Vector2


@dataclass
class MouseEvent:
  position: Vector2
  types: set[Literal['mousedown', 'mouseup']]
  