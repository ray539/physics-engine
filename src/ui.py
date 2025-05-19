from dataclasses import dataclass
from typing import Literal
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from abc import ABC, abstractmethod


class MyRect:
  top_left: Vector2
  bottom_right: Vector2
  def __init__(self, top_left: Vector2, bottom_right: Vector2) -> None:
    self.top_left = top_left
    self.bottom_right = bottom_right

class UINode(ABC):
  def __init__(self, 
               children: list['UINode'],
               padding:int = 0,
               min_width: int = 0, 
               min_height: int = 0, 
               background_color: tuple[int, int, int, int] = (0, 0, 0, 0)):
    self.children = children
    self.padding = padding
    self.min_width = min_width
    self.min_height = min_height
    self.background_color = background_color
  
  @abstractmethod
  def get_surface(self) -> tuple[Surface, Vector2]:
    """
      get real surface, as well coordinates of canvas_top_left in canvas coordinates
    """

  @abstractmethod
  def get_width(self) -> int:
    """
      get logical width for parent use
    """
  
  @abstractmethod
  def get_height(self) -> int:
    """
      get logical height for parent use
    """

class InfiniteSurface:
  """
    top left is still (0, 0) \n
    but, we are allowed to go negative and stuff
  """
  def __init__(self) -> None:
    self.objects: list[tuple[Surface, Vector2]] = [] # (UINode, top_left) pairs
  
  def blit(self, node: UINode | Surface, top_left: Vector2):
    """
      blit logical UINode top left
    """
    if isinstance(node, UINode):
      # want (0, 0) in canvas coords to -> top_left
      surf, canv_top_left = node.get_surface()
      self.objects.append((surf, canv_top_left + top_left))
    else:
      self.objects.append((node, top_left))

  def get_rects(self):
    """
      maps all child objects into rect objects
    """
    def object_to_rect(o: tuple[Surface, Vector2]):
      h = o[0].get_height()
      w = o[0].get_width()
      return MyRect(o[1], o[1] + Vector2(w, h))
    
    rects = [object_to_rect(o) for o in self.objects]
    return rects

  def get_real_surface(self):
    """
      return real surface, and coordinates of canvas top left in canvas coordinates
    """
    rects = self.get_rects()
    min_x = min([rect.top_left.x for rect in rects])
    min_y = min([rect.top_left.y for rect in rects])
    max_x = max([rect.bottom_right.x for rect in rects])
    max_y = max([rect.bottom_right.y for rect in rects])
    actual_width, actual_height = max_x - min_x, max_y - min_y
    
    surf = Surface((actual_width, actual_height), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    vec = Vector2(0, 0) - Vector2(min_x, min_y)
    
    for o in self.objects:
      surf.blit(o[0], o[1] + vec)
    pygame.draw.rect(surf, (255, 0, 0), pygame.Rect(0, 0, actual_width, actual_height), 1)
    return (surf, -vec)

def label(text: str, font_name: str, font_size: int, highlight: bool = False):
  font = pygame.font.SysFont(font_name, font_size)
  a1 = font.render(text, True, (0, 0, 0))
  b1 = pygame.Surface((a1.get_width() + 10, a1.get_height() + 10))
  b1.fill((0, 200, 0) if highlight else (200, 200, 200))
  b1.blit(a1, (5, 5))
  return b1

class ButtonWith(UINode):
  def __init__(self, 
               text: str,
               font_size: int,
               dropdown_content: UINode | None,
               font_color: tuple[int, int, int] = (0, 0, 0),
               
               font_name: str = 'Arial',
               padding: int = 5, 
               min_width: int = 0, 
               min_height: int = 0, 
               background_color: tuple[int, int, int, int] = (200, 200, 200, 255),
              ):
    super().__init__([], padding, min_width, min_height, background_color)
    self.text = text
    self.font_name = font_name,
    self.font_size = font_size
    self.font_color = font_color
    
    # self.button = self.get_button()
    self.dropdown_content = dropdown_content

  def get_button(self) -> Surface:
    font = pygame.font.SysFont(self.font_name, self.font_size)
    text_surface = font.render(self.text, True, self.font_color)
    width, height = text_surface.get_width() + 2 * self.padding, text_surface.get_height() + 2 * self.padding
    this_surface = Surface((width, height))
    this_surface.fill(self.background_color)
    this_surface.blit(text_surface, (self.padding, self.padding))
    
    # draw border. Always black for now, customize later
    pygame.draw.rect(this_surface, (0, 0, 0), pygame.Rect((0, 0), (width, height)), 2)
    return this_surface

  def get_surface(self) -> tuple[Surface, Vector2]:
    button = self.get_button()
    inf_surface = InfiniteSurface()
    inf_surface.blit(button, Vector2(0, 0))
    
    if self.dropdown_content:
      blit_x = button.get_width() - self.dropdown_content.get_width()
      blit_y = button.get_height() + 20
      
      inf_surface.blit(self.dropdown_content, Vector2(blit_x, blit_y))
    return inf_surface.get_real_surface()
  
  def get_width(self) -> int:
    button = self.get_button()
    return button.get_width()
  
  def get_height(self) -> int:
    button = self.get_button()
    return button.get_height()

ChildAlignmentType = Literal['left', 'right', 'space_between']
class Container(UINode):
  def __init__(self, 
               child_alignment: ChildAlignmentType = 'left',
               child_spacing: int = 10,
               direction: Literal['row', 'col'] = 'row',
               
               children: list[UINode] = [],
               padding:int = 10, 
               min_width: int = 0, 
               min_height: int = 0, 
               background_color: tuple[int, int, int, int] = (200, 200, 200, 255), 
              ):
    super().__init__(children, padding, min_width, min_height, background_color)
    self.child_alignment: Literal['left', 'right', 'space_between'] = child_alignment
    self.child_spacing = child_spacing
    self.direction = direction

  def get_surface(self):
    # so, we need to get the width / height of all the children
    num_children = len(self.children)
    # need to get these before hand, else don't know how to space out the nodes
    this_width = self.get_width()
    this_height = self.get_height()

    inf_surface = InfiniteSurface()
    background = Surface((this_width, this_height), pygame.SRCALPHA)
    background.fill(self.background_color)
    
    # draw background border
    pygame.draw.rect(background, (0, 0, 0), pygame.Rect((0, 0), (this_width, this_height)), 2)
    inf_surface.blit(background, Vector2(0, 0))
    
    if self.direction == 'row':
      if self.child_alignment == 'left':
        cur_top_left = Vector2(self.padding, self.padding)
        for child in self.children:
          inf_surface.blit(child, cur_top_left)
          cur_top_left += Vector2(child.get_width() + self.child_spacing, 0)
      
      elif self.child_alignment == 'right':
        cur_top_right = Vector2(this_width - self.padding, self.padding)
        for child in reversed(self.children):
          cur_top_left = cur_top_right - Vector2(child.get_width(), 0)
          inf_surface.blit(child, cur_top_left)
          cur_top_right += Vector2(-child.get_width() - self.child_spacing, 0)
          
      elif self.child_alignment == 'space_between':
        pure_width = sum([c.get_width() for c in self.children]) + self.child_spacing * (num_children - 1)
        space_left = this_width - pure_width
        cur_top_left = Vector2(space_left / 2, self.padding)
        for child in self.children:
          inf_surface.blit(child, cur_top_left)
          cur_top_left += Vector2(child.get_width() + self.child_spacing, 0)

    else:
      if self.child_alignment == 'left':
        cur_top_left = Vector2(self.padding, self.padding)
        for child in self.children:
          inf_surface.blit(child, cur_top_left)
          cur_top_left += Vector2(0, child.get_height() + self.child_spacing)
      
      elif self.child_alignment == 'right':
        cur_bottom_left = Vector2(self.padding, this_height - self.padding)
        for child in reversed(self.children):
          cur_top_left = cur_bottom_left - Vector2(0, child.get_height())
          inf_surface.blit(child, cur_top_left)
          cur_bottom_left += Vector2(0, -child.get_height() - self.child_spacing)
          
      elif self.child_alignment == 'space_between':
        pure_height = sum([c.get_height() for c in self.children]) + self.child_spacing * (num_children - 1)
        space_left = this_height - pure_height
        cur_top_left = Vector2(self.padding, space_left / 2)
        
        for child in self.children:
          inf_surface.blit(child, cur_top_left)
          cur_top_left += Vector2(0, child.get_height() + self.child_spacing)
    # now, get the actual surface
    return inf_surface.get_real_surface()

  def get_width(self) -> int:
    if self.direction == 'row':
      this_width = sum([c.get_width() for c in self.children]) + self.child_spacing * (len(self.children) - 1) + 2 * self.padding
    else:
      this_width = max([c.get_width() for c in self.children]) + 2 * self.padding

    this_width = max(this_width, self.min_width)
    return this_width
  
  def get_height(self) -> int:
    if self.direction == 'row':
      this_height = max([c.get_height() for c in self.children]) + 2 * self.padding
    else:
      this_height = sum([c.get_height() for c in self.children]) + self.child_spacing * (len(self.children) - 1) + 2 * self.padding
    
    this_height = max(this_height, self.min_height)
    return this_height
  
  def get_top_left(self, top_right: Vector2) -> Vector2:
    this_width = self.get_width()
    return Vector2(top_right.x - this_width, top_right.y)

class UILayer:
  """
    controller for the UI
  """
  def __init__(self) -> None:
    pass

  def draw(self, surface: Surface):
    pass
  
  
  # for debugging, draw only UI layer
  def play(self):
    pygame.init()
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = True
    
    load_save = Container(
      children=[
        ButtonWith(text='load', font_size=20, dropdown_content=None),
        ButtonWith(text='save', font_size=20, dropdown_content=None),
      ],
      background_color=(230, 230, 230, 255)
    )
    
    dropdown_content = Container(
      direction='col',
      children=[
        ButtonWith(text='movable items', font_size=20, dropdown_content=None),
        ButtonWith(text='all items', font_size=20, dropdown_content=None),
      ],
      background_color=(230, 230, 230, 255),
      min_height=300
    )
    
    options = Container(
      children=[
        ButtonWith(
          text='add',
          font_size=20,
          dropdown_content=None
        ),
        ButtonWith(
          text='drag',
          font_size=20,
          dropdown_content=None
        ),
        ButtonWith(
          text='delete',
          font_size=20,
          dropdown_content=None
        ),
        ButtonWith(
          text='clear..', 
          font_size=20, 
          dropdown_content=Container(
            direction='col',
            children=[
              ButtonWith(text='movable items', font_size=20, dropdown_content=None),
              ButtonWith(text='all items', font_size=20, dropdown_content=None),
            ],
            background_color=(230, 230, 230, 255),
            min_height=300
          )
        )
      ],
      child_alignment='right',
      background_color=(230, 230, 230, 255),
      padding=5
    )
    

    
    self.screen.fill((255, 255, 255))
    
    for x in range(0, SCREEN_WIDTH, 50):
      pygame.draw.line(self.screen, (200, 200, 200), Vector2(x, 0), Vector2(x, SCREEN_HEIGHT))

    surf, canvas_top_left = options.get_surface()
    self.screen.blit(surf, Vector2(300, 20) + canvas_top_left)


    pygame.display.flip()
    
    while True:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          break
      self.clock.tick(60)
    # pass