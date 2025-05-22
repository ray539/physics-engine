from abc import ABC
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

import pygame
from pygame.surface import Surface


# game state
# - add
#   - square
#   - triangle
#   - circle
# - drag
# - delete

# - upon entering 'add' game state
#   - change default selected to triangle
#     when user clicks stuff, selected is now 
# - upon entering 'drag' game state

StateName = Literal['add', 'drag', 'delete']


class State(ABC):
  pass

@dataclass(frozen=True)
class Add(State):
  selected_object: str

@dataclass(frozen=True)
class Drag(State):
  pass

@dataclass(frozen=True)
class Delete(State):
  pass

class StateManager:
  def __init__(self) -> None:
    self.prev_state: State | None = Add('triangle')
    self.current_state: State = Add('triangle')
    self.changed_frame = False
  
  def set_state(self, new_state: State):
    self.prev_state = self.current_state
    self.current_state = new_state
  
    if self.current_state != self.prev_state:
      self.changed_frame = True
    
    
def circle_graphic(side_length: int, color:tuple[int, int, int, int]=(255, 0, 0, 255)):
  circle = pygame.Surface((side_length, side_length), pygame.SRCALPHA)
  pygame.draw.circle(circle, color, (side_length / 2, side_length / 2), side_length / 2)
  return circle
  
def triangle_graphic(side_length: int, color: tuple[int, int, int, int] =(255, 0, 0, 255)):
  triag = Surface((side_length, side_length), pygame.SRCALPHA)
  pygame.draw.polygon(triag, color, [(0, side_length), (side_length, side_length), (side_length / 2, 0)])
  return triag

def square_graphic(side_length: int, color: tuple[int ,int, int, int] = (255, 0, 0, 255)):
  square = Surface((side_length, side_length), pygame.SRCALPHA)
  square.fill(color)
  return square