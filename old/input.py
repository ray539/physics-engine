
from dataclasses import dataclass

from pygame import Vector2


@dataclass
class MouseEvent:
  position: Vector2
  types: set[str]