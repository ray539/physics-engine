from abc import ABC
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

import pygame
from pygame import Surface, Vector2

from helper import world_to_screen


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

# StateName = Literal['add', 'drag', 'delete']

# for the UI
# - selected_object_id
# - and for the user, selected_object_id -> object information

# object information:
# PolygonInformation:
# - id (eg. 'default-square')
# - how do I construct this polygon?
# - points (AC order)
# CircleInformation:
# - id (eg. 'default-circle')
# - center
# - radius
# and later on when user adds extra shapes, we can add extra shapes into the 'avaliable shapes' pool with their own ids
@dataclass
class ObjectInformation:
  id: str

@dataclass
class PolygonInformation(ObjectInformation):
  
  def __init__(self, id: str, local_points: list[Vector2]):
    super().__init__(id)
    # top left is min_x, max_y
    min_x = min([p.x for p in local_points])
    max_y = max([p.y for p in local_points])
    self.local_points = [p - (min_x, max_y) for p in local_points]
    
    

@dataclass
class CircleInformation(ObjectInformation):
  radius: int

@dataclass
class State(ABC):
  pass

@dataclass
class Add(State):
  avaliable_objects: list[ObjectInformation]
  selected_id: str

@dataclass
class Drag(State):
  pass

@dataclass
class Delete(State):
  pass
 
def get_default_add_state():
  return Add(
    avaliable_objects=[
      CircleInformation(
        'default-circle', 
        50
      ),
      PolygonInformation(
        'default-triangle', 
        [
          Vector2(-50, -50),
          Vector2(50, -50),
          Vector2(0, 50) 
        ]
      ),
      PolygonInformation(
        'default-square',
        [
          Vector2(-50, -50),
          Vector2(50, -50),
          Vector2(50, 50),
          Vector2(-50, 50)
        ]
      )
    ],
    selected_id='default-circle'
  )

class StateManager:
  def __init__(self) -> None:
    
    self.ADD_STATE = get_default_add_state() # persisted between changes
    
    # self.prev_state: State | None = None
    self.current_state: State = deepcopy(self.ADD_STATE)
    # self.changed_frame = False
    self.subscribers = set[object]()
    self.state_change_notifications = set[object]()
  
  def add_subscriber(self, o: object):
    self.subscribers.add(o)
    
  def has_notification(self, o: object):
    return o in self.state_change_notifications
  
  def consume_notification(self, o: object):
    self.state_change_notifications.discard(o)
  
  def set_state(self, new_state: State):
    """
      change to new state. note, do not mutate old state
    """
    print('set_state', new_state)
    if new_state != self.current_state:
      # notify everyone
      print('  notify everyone')
      for s in self.subscribers:
        self.state_change_notifications.add(s)
        
      self.current_state = deepcopy(new_state)


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

def get_polygon_surface(points: list[Vector2], color: tuple[int, int, int, int]) -> Surface:
  """
    points: world_coordinates
  """
  
  points = world_to_screen(points)
  min_x = min([p.x for p in points])
  max_x = max([p.x for p in points])
  width = max_x - min_x
  
  min_y = min([p.y for p in points])
  max_y = max([p.y for p in points])
  height = max_y - min_y
  
  points_local = [p - (min_x, min_y) for p in points]
  surf1 = Surface((width, height), pygame.SRCALPHA)
  
  pygame.draw.polygon(surf1, color, points_local)
  return surf1

def get_width_height(points: list[Vector2]):
  """
    get width / height of smallest bounding box containing points
  """
  min_x = min([p.x for p in points])
  max_x = max([p.x for p in points])
  width = max_x - min_x
  
  min_y = min([p.y for p in points])
  max_y = max([p.y for p in points])
  height = max_y - min_y
  return (width, height)

def polygon_graphic(local_points: list[Vector2], side_length: int, color: tuple[int ,int, int, int] = (255, 0, 0, 255)):
  """
    local_points: world_coordinates
  """
  # print('polygon graphic', local_points)
  
  # squish all the points onto a 50x50 grid
  surf_poly = get_polygon_surface(local_points, color)
  width, height = surf_poly.get_width(), surf_poly.get_height()
  
  surf = Surface((side_length, side_length), pygame.SRCALPHA)
  if width >= height:
    new_width = side_length
    new_height = (height / width) * side_length
    a =  pygame.transform.scale(surf_poly, (new_width, new_height))
    space_left = side_length - new_height
    surf.blit(a, (0, space_left / 2))
  else:
    new_width = (width / height) * side_length
    new_height = side_length
    a = pygame.transform.scale(surf_poly, (new_width, new_height))
    space_left = side_length -  new_width
    surf.blit(a, (space_left / 2, 0))
    
  # print(surf.get_width(), surf.get_height())
  return surf

def label(text: str, font_name: str, font_size: int, highlight: bool = False):
  font = pygame.font.SysFont(font_name, font_size)
  a1 = font.render(text, True, (0, 0, 0))
  b1 = pygame.Surface((a1.get_width() + 10, a1.get_height() + 10))
  b1.fill((0, 200, 0) if highlight else (230, 230, 230))
  b1.blit(a1, (5, 5))
  return b1