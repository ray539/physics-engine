from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, cast
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from common import Add, Delete, Drag, StateManager, circle_graphic, square_graphic, triangle_graphic
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from abc import ABC, abstractmethod
from collections.abc import Callable
from helper import to_tuple
from input import MouseEvent
pygame.init()

@dataclass
class Drawable:
  to_draw: Surface
  dest_top_left: Vector2
  offset: Vector2
  
T = TypeVar('T')
class Controlled(Generic[T]):
  """
    wrapper to make value mutable\n
    free: whether the UINode can also set this value freely
  """
  def __init__(self, val:  T | 'Controlled[T]' | Callable[[], T], free:bool = False) -> None:
    super().__init__()
    self.free: bool = free
    self.val: T | Callable[[], T]
    
    if isinstance(val, Controlled):
      # copy 'other'
      other = cast(Controlled[T], val)
      self.val = other.val
      self.free = other.free
      
    elif isinstance(val, Callable):
      # val = cast(Callable[[], T], val)
      self.val = val
    else:
      self.val = val

  def set(self, val: T):
    """
      set value of this mutable.
    """
    self.val = val
    
  def set_if_free(self, val: T):
    """
      set value if this value is free
    """
    
    if self.free:
      self.val = val
  
  def get(self) -> T:
    if isinstance(self.val, Callable):
      return self.val() # type: ignore
    return self.val


"""
  Controlled[T] | () -> T \n
  use extract() to get the value
"""

Param = T | Controlled[T] | Callable[[], T]
"""
  Controlled[T] | () -> T. \n
  Use parse_param() to turn it into a controllable for UINode use.
"""

def parse_param(val: Param[T]) -> Controlled[T]:
  """
    given val: T | Controlled[T] | () -> T \n
    turn it into 'Controlled' type which is locked <-> the given controlled type is locked
  """
  if isinstance(val, Callable):
    val = cast(Callable[[], T], val)
    return Controlled(val)
  return Controlled(val)

def lighten(color: tuple[int, int, int, int], amount: int):
  new_color = [min(a + amount, 255) for a in color]
  new_color[3] = 255
  return tuple(new_color)

T2 = TypeVar('T2', bound='UINode')
def convert(func: Callable[[MouseEvent, T2], Any] | None, default: Callable[[MouseEvent], Any], self: T2):
  def res(mouse_event: MouseEvent):
    if func:
      func(mouse_event, self)
    else:
      default(mouse_event)
  return res

class HitBox:
  def __init__(
      self, 
      rect: pygame.Rect,
      on_mouseenter: Callable[[MouseEvent], Any] = lambda e: None,
      on_mouseleave: Callable[[MouseEvent], Any] = lambda e: None,
      on_mousepress: Callable[[MouseEvent], Any] = lambda e: None,
      on_mouserelease: Callable[[MouseEvent], Any] = lambda e: None,
      on_click: Callable[[MouseEvent], Any] = lambda e: None,
    ) -> None:
    self.rect = rect
    self.mouse_over: bool = False
    self.pressed = False
    
    self.on_mouseenter = on_mouseenter
    self.on_mouseleave = on_mouseleave
    self.on_mousepress = on_mousepress
    self.on_mouserelease = on_mouserelease
    self.on_click = on_click

  def update_mouse_over(self, mouse_event: MouseEvent, new_mouseover: bool):
    """
      update mouse_event
    """
    if new_mouseover:
      if not self.mouse_over:
        # mouse wasn't over in prev frame
        self.on_mouseenter(mouse_event)
      elif 'mousedown' in mouse_event.types:
        self.pressed = True
        self.on_mousepress(mouse_event)
      elif 'mouseup' in mouse_event.types:
        if self.pressed:
          self.on_mouserelease(mouse_event)
          self.on_click(mouse_event)
        self.pressed = False
    else:
      if self.mouse_over:
        self.on_mouseleave(mouse_event)
        self.pressed = False
    
    self.mouse_over = new_mouseover

def label(text: str, font_name: str, font_size: int, highlight: bool = False):
  font = pygame.font.SysFont(font_name, font_size)
  a1 = font.render(text, True, (0, 0, 0))
  b1 = pygame.Surface((a1.get_width() + 10, a1.get_height() + 10))
  b1.fill((0, 200, 0) if highlight else (230, 230, 230))
  b1.blit(a1, (5, 5))
  return b1

class MyRect:
  top_left: Vector2
  bottom_right: Vector2
  def __init__(self, top_left: Vector2, bottom_right: Vector2) -> None:
    self.top_left = top_left
    self.bottom_right = bottom_right

class UINode(ABC):
  def __init__(self,
               children: Param[list['UINode']],
               padding: Param[int] = Controlled(0, True),
               min_width: Param[int] = Controlled(0, True), 
               min_height: Param[int] = Controlled(0, True),
               background_color: Param[tuple[int,int,int,int]] = Controlled((200, 200, 200, 255), True)):

    self.children = parse_param(children)
    self.padding = parse_param(padding)
    self.min_width = parse_param(min_width)
    self.min_height = parse_param(min_height)
    self.background_color = parse_param(background_color)
    
    # to be filled in
    self.is_wh_calculated = False
    self.width_height: tuple[int, int] = (-1, -1)
    
    self.is_gr_calculated = False
    self.global_rect: pygame.Rect = pygame.Rect((-1, -1), (-1, -1))
  
  @abstractmethod
  def calc_width_height(self) -> tuple[int, int]:
    """
      set self.width_height to appropiate values for parent use\n
      return (width, height)
    """
    
  @abstractmethod
  def get_drawable(self, top_left: Vector2) -> Drawable:
    """
      calculate hitboxes for node and children \n
      and return drawable
    """
    pass
  
  @abstractmethod
  def get_best_hitbox(self, mouse_event: MouseEvent) -> HitBox | None:
    """
      given a mouse event, get best hitbox from this node and it's children
    """
  
  @abstractmethod
  def get_all_hitboxes(self) -> list[HitBox]:
    """
      get all hitboxes from tree rooted at this node
    """

# Controlled[]
# a = Controlled(1)
# a.set(2)
# a.set(3)
# a.set(4)
# ...
# and, we will



class InfiniteSurface:
  """
    top left is still (0, 0) \n
    but, we are allowed to go negative and stuff
  """
  def __init__(self) -> None:
    self.objects: list[tuple[Surface, Vector2]] = [] # (UINode, top_left) pairs
  
  def blit(self, surface: Surface, top_left: Vector2):
    """
      blit logical UINode top left
    """
    self.objects.append((surface, top_left))

  def get_child_rects(self):
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
    rects = self.get_child_rects()
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
    # pygame.draw.rect(surf, (255, 0, 0), pygame.Rect(0, 0, actual_width, actual_height), 1) # for debuggging, red line
    return (surf, -vec)

class ButtonWith(UINode):
  def __init__(self, 
               dropdown_content: UINode | None,
               
               text: Param[str] = Controlled('', True),
               font_size: Param[int] = Controlled(20, True),
               font_name: Param[str] = Controlled('Arial', True),
               
               show_dropdown: Param[bool] = Controlled(False, True),
               
               font_color: Param[tuple[int, int, int]] = Controlled((0, 0, 0), True),
               gap: Param[int] = Controlled(20, True),
               on_mouseenter: Callable[[MouseEvent, 'ButtonWith'], Any] | None = None,
               on_mouseleave: Callable[[MouseEvent, 'ButtonWith'], Any] | None = None,
               on_mousepress: Callable[[MouseEvent, 'ButtonWith'], Any] | None = None,
               on_mouserelease: Callable[[MouseEvent, 'ButtonWith'], Any] | None = None,
               on_click: Callable[[MouseEvent, 'ButtonWith'], Any] | None = None,
               
               padding: int = 5, 
               min_width: int = 0, 
               min_height: int = 0,
               background_color: Param[tuple[int,int,int,int]] = Controlled((200, 200, 200, 255), True), # controlled / uncontrolled
              ):
    super().__init__([], padding, min_width, min_height, background_color)
    self.text = parse_param(text)
    self.font_name = parse_param(font_name)
    self.font_size = parse_param(font_size)
    self.font_color = parse_param(font_color)
    self.gap = parse_param(gap)
    
    self.DROPDOWN_CONTENT = dropdown_content
    self.show_dropdown = parse_param(show_dropdown)
    
    self.background_shade: Literal['normal', 'lighter', 'darker'] = 'normal'
    def on_mouseenter_default(mouse_event: MouseEvent):
      # make it a bit lighter
      self.background_shade = 'lighter'

    def on_mouseleave_default(mouse_event: MouseEvent):
      self.background_shade = 'normal'
      # set_if_controlled(self.background_color, extract(self.ORIGINAL_BGC))
    
    def on_mousepress_default(mouse_event: MouseEvent):
      # make it a bit darker
      self.background_shade = 'darker'
      
    def on_mouserelease_default(mouse_event: MouseEvent):
      self.background_shade = 'normal'
    
    def on_click_default(mouse_event: MouseEvent):
      self.show_dropdown.set_if_free(not self.show_dropdown.get())
      if on_click:
        on_click(mouse_event, self)

    # to be calculated
    self.button_hitbox: HitBox = HitBox(
      pygame.Rect((-1, -1), (-1, -1)),
      on_mouseenter=convert(on_mouseenter, on_mouseenter_default, self),
      on_mouseleave=convert(on_mouseleave, on_mouseleave_default, self),
      on_mousepress=convert(on_mousepress, on_mousepress_default, self),
      on_mouserelease=convert(on_mouserelease, on_mouserelease_default, self),
      on_click=on_click_default
    )

  def get_button(self) -> Surface:
    if self.background_shade == 'normal':
      background_color = self.background_color.get()
    elif self.background_shade == 'darker':
      background_color = lighten(self.background_color.get(), -20)
    else:
      background_color = lighten(self.background_color.get(), 20)      
    
    font = pygame.font.SysFont(self.font_name.get(), self.font_size.get())
    text_surface = font.render(self.text.get(), True, self.font_color.get())
    width, height = text_surface.get_width() + 2 * self.padding.get(), text_surface.get_height() + 2 * self.padding.get()
    this_surface = Surface((width, height))
    this_surface.fill(background_color)
    this_surface.blit(text_surface, (self.padding.get(), self.padding.get()))
    # draw border. Always black for now, customize later
    pygame.draw.rect(this_surface, (0, 0, 0), pygame.Rect((0, 0), (width, height)), 2)
    return this_surface
  
  def calc_width_height(self):
    button = self.get_button()
    width, height = button.get_width(), button.get_height()
    
    dropdown_content = self.DROPDOWN_CONTENT if self.show_dropdown.get() else None
    if dropdown_content:
      dropdown_content.calc_width_height()
    
    self.width_height = (width, height)
    self.is_wh_calculated = True
    return (width, height)
  
  def get_best_hitbox(self, mouse_event: MouseEvent):
    # try to get from dropdown content first
    dropdown_content = self.DROPDOWN_CONTENT if self.show_dropdown.get() else None
    if dropdown_content:
      tmp = dropdown_content.get_best_hitbox(mouse_event)
      if tmp:
        return tmp

    # get it from myself
    if self.button_hitbox.rect.collidepoint(mouse_event.position):
      return self.button_hitbox
    return None
  
  def get_all_hitboxes(self):
    # get all hitboxes from myself and children
    ans = [self.button_hitbox]
    dropdown_content = self.DROPDOWN_CONTENT if self.show_dropdown.get() else None
    if dropdown_content:
      ans.extend(dropdown_content.get_all_hitboxes())
    return ans
  
  def get_drawable(self, top_left: Vector2) -> Drawable:
    if not self.is_wh_calculated:
      raise Exception('you must run calculate wh first')    
    inf_surface = InfiniteSurface()
    button = self.get_button()
    inf_surface.blit(button, Vector2(0, 0))
    
    button_rect = button.get_rect()
    button_rect.topleft = to_tuple(top_left)
    self.button_hitbox.rect = button_rect

    dropdown_content = self.DROPDOWN_CONTENT if self.show_dropdown.get() else None    
    if dropdown_content:
      blit_x = button.get_width() - dropdown_content.width_height[0]
      blit_y = button.get_height() + self.gap.get()
      ret = dropdown_content.get_drawable(Vector2(blit_x, blit_y) + top_left)
      inf_surface.blit(ret.to_draw, Vector2(blit_x, blit_y))
    
    surf, offset = inf_surface.get_real_surface()
    self.global_rect = surf.get_rect()
    self.global_rect.topleft = to_tuple(top_left + offset)
    self.is_gr_calculated = True
    return Drawable(surf, top_left, offset)

class MySurface(UINode):
  def __init__(self,    
               surface: pygame.Surface,
               
               show_outline: Param[bool] = Controlled(False, True),
               on_click: Callable[[MouseEvent, 'MySurface'], Any] | None = None,
               children: list[UINode] = [],
               padding: int = 0, 
               min_width: int = 0, 
               min_height: int = 0, 
               background_color: Param[tuple[int, int, int, int]] = (0, 0, 0, 0)
  ):
    super().__init__(children, padding, min_width, min_height, background_color)
    
    self.ORIGINAL_SURF = surface
    self.OUTLINED_SURF = surface.copy()
    
    self.show_outline = parse_param(show_outline)
    
    pygame.draw.rect(self.OUTLINED_SURF, (0, 255, 0, 255), pygame.Rect((0, 0), (self.OUTLINED_SURF.get_width(), self.OUTLINED_SURF.get_height())), 2)
    self.hit_box = HitBox(
      pygame.Rect((-1, -1), (-1, -1)),
      on_click=convert(on_click, lambda e: None, self)
    )
  
  def calc_width_height(self) -> tuple[int, int]:
    surface = self.OUTLINED_SURF if self.show_outline.get() else self.ORIGINAL_SURF
    w,h = surface.get_width(), surface.get_height()
    self.width_height = (w, h)
    return (w, h)

  def get_drawable(self, top_left: Vector2) -> Drawable:
    surface = self.OUTLINED_SURF if self.show_outline.get() else self.ORIGINAL_SURF
    self.hit_box.rect = pygame.Rect(top_left, (surface.get_width(), surface.get_height()))
    return Drawable(surface, top_left, Vector2(0, 0))

  def get_best_hitbox(self, mouse_event: MouseEvent) -> HitBox | None:
    if self.hit_box.rect.collidepoint(mouse_event.position):
      return self.hit_box
    return None

  def get_all_hitboxes(self) -> list[HitBox]:
    return [self.hit_box]

ChildAlignmentType = Literal['left', 'right', 'space_between']
class Container(UINode):
  def __init__(self,
               child_alignment: ChildAlignmentType = 'left',
               child_spacing: int = 10,
               direction: Literal['row', 'col'] = 'row',
               children: list[UINode] = [],
               padding: int = 10, 
               min_width: int = 0, 
               min_height: int = 0, 
               background_color: Param[tuple[int,int,int,int]] = (200, 200, 200, 255), 
              ):
    super().__init__(children, padding, min_width, min_height, background_color)
    
    self.child_alignment: Literal['left', 'right', 'space_between'] = child_alignment
    self.child_spacing = child_spacing
    self.direction = direction
    
    self.container_hitbox = HitBox(
      pygame.Rect((-1, -1), (-1, -1)),
    )
  
  def process_mouse_event_self(self, mouse_event: MouseEvent) -> bool:
    return False
  
  def calc_width_height(self):
    child_width_heights = [c.calc_width_height() for c in self.children.get()]
    num_children = len(self.children.get())
    main_dir = 0 if self.direction == 'row' else 1
    width_height = [0, 0]
    
    width_height[main_dir] = sum([c[main_dir] for c in child_width_heights]) + self.child_spacing * max(num_children - 1, 0) + 2 * self.padding.get()
    width_height[1 - main_dir] = max([c[1 - main_dir] for c in child_width_heights]) + 2 * self.padding.get()
    width_height[0] = max(width_height[0], self.min_width.get())
    width_height[1] = max(width_height[1], self.min_height.get())
    self.width_height = cast(tuple[int, int], tuple(width_height))
    
    self.is_wh_calculated = True
    return self.width_height
  
  def get_drawable(self, top_left: Vector2) -> Drawable:
    if not self.is_wh_calculated:
      raise Exception('you must run calculate_with_height first')

    main_dir = 0 if self.direction == 'row' else 1
    dirs = [Vector2(1, 0), Vector2(0, 1)]
    delta = [Vector2(-1, 1), Vector2(1, -1)]
    
    num_children = len(self.children.get())
    # need to get these before hand, else don't know how to space out the nodes
    background = Surface(self.width_height, pygame.SRCALPHA)
    background.fill(self.background_color.get())
    pygame.draw.rect(background, (0, 0, 0), pygame.Rect((0, 0), self.width_height), 2)
    
    inf_surface = InfiniteSurface()
    inf_surface.blit(background, Vector2(0, 0))
    
    if self.child_alignment == 'left':
      cur_top_left = Vector2(self.padding.get(), self.padding.get())
      for child in self.children.get():
        ret = child.get_drawable(cur_top_left + top_left)
        inf_surface.blit(ret.to_draw, cur_top_left + ret.offset)
        cur_top_left += dirs[main_dir] * (child.width_height[main_dir] + self.child_spacing)   
    
    elif self.child_alignment == 'right':
      cur_pt = self.width_height[main_dir] * dirs[main_dir] + delta[main_dir] * self.padding.get()
      
      for child in reversed(self.children.get()):
        cur_top_left = cur_pt - dirs[main_dir] * child.width_height[main_dir]
        ret = child.get_drawable(cur_top_left + top_left)
        inf_surface.blit(ret.to_draw, cur_top_left + ret.offset)
        cur_pt -= dirs[main_dir] * (child.width_height[main_dir] + self.child_spacing)
        
    elif self.child_alignment == 'space_between':
      pure_length = sum([c.width_height[main_dir] for c in self.children.get()]) + self.child_spacing * (num_children - 1)

      space_left = self.width_height[main_dir] - pure_length - 2*self.padding.get()
      cur_top_left = Vector2(self.padding.get(), self.padding.get()) + dirs[main_dir] * (space_left / 2)
      
      for child in self.children.get():
        ret = child.get_drawable(cur_top_left + top_left)
        inf_surface.blit(ret.to_draw, cur_top_left + ret.offset)
        cur_top_left += child.width_height[main_dir] * dirs[main_dir]
    
    this_to_draw, this_offset = inf_surface.get_real_surface()
    self.global_rect = this_to_draw.get_rect()
    self.global_rect.topleft = to_tuple(top_left + this_offset)
    self.is_gr_calculated = True
    
    self.container_hitbox.rect = pygame.Rect(to_tuple(top_left), self.width_height)
    
    return Drawable(this_to_draw, top_left, this_offset)
  
  def get_all_hitboxes(self) -> list[HitBox]:
    ans = [self.container_hitbox]
    for c in self.children.get():
      ans.extend(c.get_all_hitboxes())
    return ans
  
  def get_best_hitbox(self, mouse_event: MouseEvent) -> HitBox | None:
    for c in self.children.get():
      tmp = c.get_best_hitbox(mouse_event)
      if tmp:
        return tmp
    if self.container_hitbox.rect.collidepoint(mouse_event.position):
      return self.container_hitbox
      
    return None

class PositionedUINode:
  def __init__(self, node: UINode, dest_top_left: Vector2 | Callable[[UINode], Vector2]) -> None:
    self.node = node
    self.node.calc_width_height()
    if isinstance(dest_top_left, Callable):
      dest_top_left = dest_top_left(node)
    self.dest_top_left = dest_top_left
  
  def draw_node(self, dest_surface: Surface):
    self.node.calc_width_height()
    drawable = self.node.get_drawable(self.dest_top_left)
    dest_surface.blit(drawable.to_draw, drawable.dest_top_left + drawable.offset)
  
# process clicks
# pressed
# - mouse hovering, mouse_down
# 
# mouse_enter:
# - not prev_mouse_over
# - yes current_mouse_over

# if pressed, 
# - mouse leave -> pressed = false

# node = get_mouse_hovering(mouse_pos)
#   set mouse_hovering for rest of the nodes

MouseEventTypes = Literal['mouseenter', 'mouseleave', 'press', 'click']


def init_node(node: UINode, dest_top_left: Vector2 | Callable[[UINode], Vector2]):
  """
    dest_top_left: top_left to blit node, or a function which returns one\n
    calculate metadata about the UINode, and return a drawable
  """
  node.calc_width_height()
  if isinstance(dest_top_left, Callable):
    dest_top_left = dest_top_left(node)
  return node.get_drawable(dest_top_left)



class UILayer:
  """
    controller for the UI
  """
  def __init__(self, global_state: StateManager, engine: Any) -> None:        
    self.global_state = global_state
    
    options = Container(
      direction='col',
      child_spacing=0,
      padding=0,
      children=[
        Container(
          child_alignment='space_between',
          min_width=300,
          padding=2,
          children=[
            MySurface(
              label('select mode', 'Arial', 15)
            )
          ]
        ),
        Container(
          children=[
            ButtonWith(
              text='add',
              font_size=20,
              gap=10,
              background_color=lambda: (255, 200, 200, 255) if isinstance(global_state.current_state, Add) else (200, 200, 200, 255),
              on_click=lambda e, n: global_state.set_state(Add('triangle')),
              dropdown_content=Container(
                background_color=Controlled((230, 230, 230, 255)),
                child_alignment='left',
                children=[
                  Container(
                    padding=10,
                    background_color=(200, 200, 200, 255),
                    children=[
                      MySurface(
                        surface=circle_graphic(50),
                        show_outline= lambda: isinstance(global_state.current_state, Add) and global_state.current_state.selected_object == 'circle',
                        on_click= lambda e, n: global_state.set_state(Add('circle'))
                      ),
                      MySurface(
                        surface=triangle_graphic(50),
                        show_outline= lambda : isinstance(global_state.current_state, Add) and global_state.current_state.selected_object == 'triangle',
                        on_click = lambda e, n:global_state.set_state(Add('triangle'))
                      ),
                      MySurface(
                        surface=square_graphic(50),
                        show_outline=lambda: isinstance(global_state.current_state, Add) and global_state.current_state.selected_object == 'square',
                        on_click=lambda e, n: global_state.set_state(Add('square'))
                      )
                    ]
                  ),
                  ButtonWith(
                    text='more..',
                    dropdown_content=None,
                    font_size=20
                  )
                ],
                padding=10,
                child_spacing=10
              ),
            ),
            ButtonWith(
              text='drag',
              font_size=20,
              background_color=lambda: (255, 200, 200, 255) if isinstance(global_state.current_state, Drag) else (200, 200, 200, 255),
              on_click=lambda e,n: global_state.set_state(Drag()),
              dropdown_content=None
            ),
            ButtonWith(
              text='delete',
              font_size=20,
              background_color=lambda: (255, 200, 200, 255) if isinstance(global_state.current_state, Delete) else (200, 200, 200, 255),
              on_click=lambda e,n: global_state.set_state(Delete()),
              dropdown_content=None
            ),
            ButtonWith(
              text='clear..', 
              font_size=20, 
              gap=10,
              dropdown_content=Container(
                direction='col',
                children=[
                  ButtonWith(text='movable items', font_size=20, dropdown_content=None, on_click=lambda e, n: engine.remove_movable_bodies()),
                  ButtonWith(text='all items', font_size=20, dropdown_content=None),
                ],
                background_color=(230, 230, 230, 255),
                min_height=300,
                padding=5
              )
            )
          ],
          child_alignment='right',
          background_color=(230, 230, 230, 255),
          padding=5,
          min_width=300
        )
      ]
    )
    options = PositionedUINode(
      options,
      lambda n: Vector2(SCREEN_WIDTH - n.width_height[0] - 20, 20)
    )
    load_save = Container(
      child_alignment='left',
      background_color=(230, 230, 230, 255),
      padding=5,
      min_width=300,
      children=[
        ButtonWith(
          text='load',
          dropdown_content=None,
        ),
        ButtonWith(
          text='save',
          dropdown_content=None
        ),
      ]
    )
    load_save = PositionedUINode(load_save, Vector2(20, 20))
    self.positioned_nodes = [options, load_save]

  def handle_input(self, mouse_event: MouseEvent):
    """
      consume the mouse_event. \n
      return the mouse_event if unconsumed, else noen
    """
    best = None
    for p_node in self.positioned_nodes:
      best = p_node.node.get_best_hitbox(mouse_event)
      if best:
        break
    
    all_hitboxes = [h for p_node in self.positioned_nodes for h in p_node.node.get_all_hitboxes()]
    for h in all_hitboxes:
      h.update_mouse_over(mouse_event, h == best)
    
    return mouse_event if (best == None) else None
  
  def draw(self, surface: Surface):
    for p_node in self.positioned_nodes:
      p_node.draw_node(surface)
  
  # for debugging, draw only UI layer
  def play(self):
    
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = True
    self.mouse_down = False
    while self.running:      
      mouse_pos_frame = Vector2(pygame.mouse.get_pos())
      mouse_event: MouseEvent = MouseEvent(mouse_pos_frame, set())
      
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          
        if event.type == pygame.MOUSEBUTTONDOWN:
          mouse_event.types.add('mousedown')
          self.mouse_down = True
        
        if event.type == pygame.MOUSEBUTTONUP:
          mouse_event.types.add('mouseup')
          self.mouse_down = False

      # process mouse events
      self.handle_input(mouse_event)
      
      # draw nodes
      self.screen.fill((255, 255, 255))
      for x in range(0, SCREEN_WIDTH, 50):
        pygame.draw.line(self.screen, (200, 200, 200), Vector2(x, 0), Vector2(x, SCREEN_HEIGHT))
        
      self.draw(self.screen)
      pygame.display.flip()
      self.clock.tick(60)