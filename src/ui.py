from dataclasses import dataclass
from typing import Literal
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from abc import ABC, abstractmethod

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
  def get_node(self) -> Surface: ...


def label(text: str, font_name: str, font_size: int, highlight: bool = False):
  font = pygame.font.SysFont(font_name, font_size)
  a1 = font.render(text, True, (0, 0, 0))
  b1 = pygame.Surface((a1.get_width() + 10, a1.get_height() + 10))
  b1.fill((0, 200, 0) if highlight else (200, 200, 200))
  b1.blit(a1, (5, 5))
  return b1

class ButtonWithDropdown(UINode):
  def __init__(self):
    
    
    pass

  def get_node(self) -> Surface: ...

ChildAlignmentType = Literal['left', 'right', 'space_between']

class Container(UINode):
  def __init__(self, 
               children: list[UINode], 
               padding:int = 0, 
               min_width: int = 0, 
               min_height: int = 0, 
               background_color: tuple[int, int, int, int] = (0, 0, 0, 0), 
               
               child_alignment: ChildAlignmentType = 'left',
               child_spacing: int = 10
              ):
    super().__init__(children, padding, min_width, min_height, background_color)
    self.child_alignment: Literal['left', 'right', 'space_between'] = child_alignment
    self.child_spacing = child_spacing

  def get_node(self):
    # so, we need to get the width / height of all the children
    this_node = Surface((100, 100))
    child_nodes = [child.get_node() for child in self.children]
    num_children = len(child_nodes)
    
    this_width = sum([c.get_width() for c in child_nodes]) + self.child_spacing * (num_children - 1) + 2 * self.padding
    this_width = max(this_width, self.min_width)
    this_height = max([c.get_height() for c in child_nodes]) + 2 * self.padding
    this_height = max(this_height, self.min_height)
    this_node = Surface((this_width, this_height), pygame.SRCALPHA) # makes container alpha suspectible
    this_node.fill(self.background_color)
    
    if self.child_alignment == 'left':
      cur_top_left = Vector2(self.padding, self.padding)
      for child_node in child_nodes:
        this_node.blit(child_node, cur_top_left)
        cur_top_left += Vector2(child_node.get_width() + self.child_spacing, 0)
    
    elif self.child_alignment == 'right':
      cur_top_right = Vector2(this_width - self.padding, self.padding)
      for child_node in child_nodes:
        cur_top_left = cur_top_right - Vector2(-child_node.get_width(), 0)
        this_node.blit(child_node, cur_top_left)
        cur_top_right += Vector2(-child_node.get_width() - self.child_spacing, 0)
        
    elif self.child_alignment == 'space_between':
      pure_width = sum([c.get_width() for c in child_nodes]) + self.child_spacing * (num_children - 1)
      space_left = this_width - pure_width
      cur_top_left = Vector2(space_left / 2, self.padding)
      for child_node in child_nodes:
        this_node.blit(child_node, cur_top_left)
        cur_top_left += Vector2(child_node.get_width() + self.child_spacing, 0)
  
    return this_node


  

class UILayer:
  """
    controller for the UI
  """
  def __init__(self) -> None:
    
    
    pass

  def draw(self, surface: Surface):
          # draw the UI here
    l1 = label('1: add square', 'Arial', 36, False)
    surface.blit(l1, (10, 10))
    left = l1.get_rect().bottomright[0]
    print(left)
    
    l2 = label('2: drag', 'Arial', 36, True)
    surface.blit(l2, (left + 20, 10))
  
  
  # for debugging, draw only UI layer
  def play(self):
    pygame.init()
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = True
    
    while self.running:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          break
      
      self.screen.fill((255, 255, 255))
      for x in range(0, SCREEN_WIDTH, 50):
        pygame.draw.line(self.screen, (200, 200, 200), Vector2(x, 0), Vector2(x, SCREEN_HEIGHT))

      pygame.display.flip()
      self.clock.tick(60)
    pass