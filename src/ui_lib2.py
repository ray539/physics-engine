
from abc import ABC, abstractmethod
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, cast
from pygame import Rect, Surface, Vector2
import pygame

from common import StateManager
from helper import to_tuple

@dataclass
class MouseEvent:
  position: Vector2
  type: Literal['mousedown', 'mouseup', 'none']

@dataclass
class Drawable:
  to_draw: Surface
  blit_offset: Vector2 # if you want to draw it at 'dest', you need to blit it at 'dest + blit_offset'

T = TypeVar('T')

class CACHE_EMPTY:
  """
    marker class for empty cache \n
    (since we can't use None)
  """
  pass

class Controlled(Generic[T]):
  def __init__(self, getter_func: Callable[[], T], free: bool = False) -> None:
    super().__init__()
    self.getter_func = getter_func
    self.free = free
    self.cache: T | CACHE_EMPTY = getter_func()

  def cache_clear(self):
    self.cache = CACHE_EMPTY()

  def set(self, new_getter_func: Callable[[], T]):
    if self.free:
      self.getter_func = new_getter_func
  
  def get(self) -> T:
    if isinstance(self.cache, CACHE_EMPTY):
      self.cache = self.getter_func()
    return self.cache


class Expr(Generic[T]):
  def __init__(self, eval_func: Callable[[], T]) -> None:
    self.eval_func = eval_func
  
  def eval(self) -> T:
    return self.eval_func()  

Param = T | Controlled[T] | Expr[T]
# parse in what the user gives
# also, handle default parameters


# user might give
# - outline = lambda: curr_state == add
# - on_click = lambda: ....
# - these lambda's should be treated differently
# - how?


def parse_param(param: Param[T]) -> Controlled[T]:
  if isinstance(param, Expr):
    param = cast(Expr[T], param)
    return Controlled(param.eval)
  elif isinstance(param, Controlled):
    param = cast(Controlled[T], param)
    return deepcopy(param) # in case default parameters. Make sure controlled is deepcopyable

  param = cast(T, param)
  return Controlled(lambda: param) # if we give a surface, it


class HitBox:
  def __init__(
      self, 
      owner: 'object',
      rect: Rect,
      on_mouseenter: Callable[[MouseEvent], Any] = lambda e: None,
      on_mouseleave: Callable[[MouseEvent], Any] = lambda e: None,
      on_mousepress: Callable[[MouseEvent], Any] = lambda e: None,
      on_mouserelease: Callable[[MouseEvent], Any] = lambda e: None,
      on_click: Callable[[MouseEvent], Any] = lambda e: None,
    ) -> None:
    self.owoner = owner
    self.rect = rect    
    self.on_mouseenter = on_mouseenter
    self.on_mouseleave = on_mouseleave
    self.on_mousepress = on_mousepress
    self.on_mouserelease = on_mouserelease
    self.on_click = on_click
    
    
    self.mouse_over_: bool = False
    self.pressed_ = False

  def update(self, mouse_event: MouseEvent, new_mouseover: bool):
    """
      update hitbox status based on whether new mouse is over the hitbox
    """
    if new_mouseover:
      if not self.mouse_over_:
        # mouse wasn't over in prev frame
        self.on_mouseenter(mouse_event)
      elif mouse_event.type == 'mousedown':
        self.pressed_ = True
        self.on_mousepress(mouse_event)
      elif mouse_event.type == 'mouseup':
        if self.pressed_:
          self.on_mouserelease(mouse_event)
          self.on_click(mouse_event)
        self.pressed_ = False
    else:
      if self.mouse_over_:
        self.on_mouseleave(mouse_event)
        self.pressed_ = False
    self.mouse_over_ = new_mouseover

@dataclass
class MyRect:
  top_left: Vector2
  bottom_right: Vector2

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

  def get_drawable(self):
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
    return Drawable(surf, -vec)


T3 = TypeVar('T3', bound='UINode')
AlphaColor = tuple[int, int, int, int]

class UINode(ABC):
  def __init__(self,
               children: Param[list[T3]] = Controlled(lambda: []),
               padding: Param[int] = Controlled(lambda: 0),
               min_width: Param[int] = Controlled(lambda: 0),
               min_height: Param[int] = Controlled(lambda: 0),
               background_color: Param[AlphaColor] = Controlled(lambda: (0, 0, 0, 0), True),
               id: str = 'none',
              ):
  
    self.children = parse_param(children)
    self.padding = parse_param(padding)
    self.min_width = parse_param(min_width)
    self.min_height = parse_param(min_height)
    self.background_color = parse_param(background_color)
    
    self.id = id
    
    # to be filled in
    self._width_height: tuple[int, int] | None = None
    self._drawable: Drawable | None = None


  @abstractmethod
  def calc_width_height(self):
    """
      calculate and store width height of myself and my children
    """
  
  def uncache_width_height(self):
    """
      set self._width_height to Null for me and my children
    """
    for attr_name in self.__dict__:
      attr_val = getattr(self, attr_name)
      if isinstance(attr_val, Controlled):
        val = attr_val.get() # type: ignore
        if isinstance(val, UINode):
          val.uncache_width_height()
        
    for c in self.children.get():
      c.uncache_width_height()
    self._width_height = None
    
  def get_width_height(self) -> tuple[int, int]:
    """
      get width height of child if it's calculated, else calculate it on the spot
    """
    if self._width_height == None:
      self.calc_width_height()
    if self._width_height == None:
      raise Exception('wtf')
    
    return self._width_height
  
  def set_width_height(self, val: tuple[int, int]):
    self._width_height = val
  
  def set_drawable(self, val: Drawable):
    self._drawable = val
  
  def get_drawable(self) -> Drawable:
    if not self._width_height or not self._drawable:
      raise Exception('node is not ready to be drawn')
    return self._drawable
  
  def get_all_hitboxes(self) -> list[HitBox]:
    """
      get all hitboxes of:
      - any parameter of type 'HitBox'
      - this node's children
    """
    res: list[HitBox] = []
    for attr_name in self.__dict__:
      attr_val = getattr(self, attr_name)
      if isinstance(attr_val, HitBox):
        res.append(attr_val)
      elif isinstance(attr_val, Controlled):
        val = attr_val.get() # type: ignore
        if isinstance(val, UINode):
          res.extend(val.get_all_hitboxes())
    for c in self.children.get():
      res.extend(c.get_all_hitboxes())
    return res
  
  def get_best_hitbox(self, mouse_event: MouseEvent) -> HitBox | None:
    # UINode attribute hitboxes
    for attr_name in self.__dict__:
      attr_val = getattr(self, attr_name)
      if isinstance(attr_val, Controlled):
        val = attr_val.get() # type: ignore
        if isinstance(val, UINode):
          a = val.get_best_hitbox(mouse_event)
          if a:
            return a
    # children hitboxes
    for c in self.children.get():
      a = c.get_best_hitbox(mouse_event)
      if a:
        return a

    # my hitboxes
    for attr_name in self.__dict__:
      attr_val = getattr(self, attr_name)
      if isinstance(attr_val, HitBox):
        if attr_val.rect.collidepoint(mouse_event.position):
          return attr_val
    return None


  @abstractmethod
  def recalc_drawable_and_hitbox(self, top_left: Vector2) -> Drawable:
    pass
  
  def recalculate_drawable_and_hitbox(self, top_left: Vector2 | Callable[['UINode'], Vector2]) -> Drawable:
    """
      caclulate and cache the following items\n
      - my drawable
      - my hitboxes \n
      return drawable of myself
    """
    self.uncache_width_height()
    if isinstance(top_left, Callable):
      top_left = top_left(self)
    return self.recalc_drawable_and_hitbox(top_left)
  
  def clear_caches(self):
    """
      clear the cache of all 'controlled' attributes in this object
    """
    for attr_name in self.__dict__:
      attr_val = getattr(self, attr_name)
      if isinstance(attr_val, Controlled):
        attr_val.cache_clear()



def lighten(color: AlphaColor, amount: int) -> AlphaColor:
  new_color = [min(a + amount, 255) for a in color]
  new_color[3] = 255
  return tuple(new_color) # type: ignore


T2 = TypeVar('T2', bound='UINode')
def convert(func: Callable[[MouseEvent, T2], Any] | None, default: Callable[[MouseEvent], Any], self: T2):
  def res(mouse_event: MouseEvent):
    if func:
      func(mouse_event, self)
    else:
      default(mouse_event)
  return res

class ButtonWith(UINode):
  def __init__(self, 
               dropdown_content: Param[UINode | None] = None,
               show_dropdown: Param[bool] = Controlled(lambda: False, free=True),
               
               text: Param[str] = '',
               font_size: Param[int] = 20,
               font_name: Param[str] = 'Arial',
               font_color: Param[AlphaColor] = (0, 0, 0, 255),
               gap: Param[int] = 20,
               
               on_mouseenter: Param[Callable[[MouseEvent, 'ButtonWith'], Any] | None] = None,
               on_mouseleave: Param[Callable[[MouseEvent, 'ButtonWith'], Any] | None] = None,
               on_mousepress: Param[Callable[[MouseEvent, 'ButtonWith'], Any] | None] = None,
               on_mouserelease: Param[Callable[[MouseEvent, 'ButtonWith'], Any] | None] = None,
               on_click: Param[Callable[[MouseEvent, 'ButtonWith'], Any] | None] = None,
              
               padding: int = 5, 
               min_width: int = 0, 
               min_height: int = 0,
               background_color: Param[AlphaColor] = (200, 200, 200, 255),
               id: str = 'none'
            ):
    super().__init__([], padding, min_width, min_height, background_color, id)
    self.dropdown_content = parse_param(dropdown_content)
    self.show_dropdown = parse_param(show_dropdown)
    self.text = parse_param(text)
    self.font_size = parse_param(font_size)
    self.font_name = parse_param(font_name)
    self.font_color = parse_param(font_color)
    self.gap = parse_param(gap)
    
    self.on_mouseenter = parse_param(on_mouseenter)
    self.on_mouseleave = parse_param(on_mouseleave)
    self.on_mousepress = parse_param(on_mousepress)
    self.on_mouserelease = parse_param(on_mouserelease)
    self.on_click = parse_param(on_click)
    
    self.background_shade_: Literal['normal', 'lighter', 'darker'] = 'normal'
    
    def on_mouseenter_(mouse_event: MouseEvent):
      f = self.on_mouseenter.get()
      if f:
        f(mouse_event, self)
        return
      # make it a bit lighter
      self.background_shade_ = 'lighter'

    def on_mouseleave_(mouse_event: MouseEvent):
      f = self.on_mouseleave.get()
      if f:
        f(mouse_event, self)
        return
      self.background_shade_ = 'normal'
      
    
    def on_mousepress_(mouse_event: MouseEvent):
      f = self.on_mousepress.get()
      if f:
        f(mouse_event, self)
        return
      # make it a bit darker
      self.background_shade_ = 'darker'
      
    def on_mouserelease_(mouse_event: MouseEvent):
      f = self.on_mouserelease.get()
      if f:
        f(mouse_event, self)
        return
      # change back to normal
      self.background_shade_ = 'normal'
    
    def on_click_(mouse_event: MouseEvent):
      a = not self.show_dropdown.get()
      self.show_dropdown.set(lambda: a)
      self.clear_caches() # force rerender
      on_click = self.on_click.get()
      
      if on_click:
        on_click(mouse_event, self)
    
    self.button_hitbox_ = HitBox(
      owner = self,
      rect = Rect((-1, -1), (-1, -1)),
      on_mouseenter=on_mouseenter_,
      on_mouseleave=on_mouseleave_,
      on_mousepress=on_mousepress_,
      on_mouserelease=on_mouserelease_,
      on_click=on_click_
    )
  
  def get_best_hitbox(self, mouse_event: MouseEvent) -> HitBox | None:
    # override parent
    dropdown_content = self.dropdown_content.get() if self.show_dropdown.get() else None
    if dropdown_content:
      tmp = dropdown_content.get_best_hitbox(mouse_event)
      if tmp:
        return tmp
    
    if self.button_hitbox_.rect.collidepoint(mouse_event.position):
      return self.button_hitbox_
    
    return None
  
  def get_all_hitboxes(self) -> list[HitBox]:
    # override parent
    res = [self.button_hitbox_]
    dropdown_content = self.dropdown_content.get() if self.show_dropdown.get() else None
    if dropdown_content != None:
      res.extend(dropdown_content.get_all_hitboxes())
    return res
    
  def get_button(self) -> Surface:
    if self.background_shade_ == 'normal':
      background_color = self.background_color.get()
    elif self.background_shade_ == 'darker':
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
    self.set_width_height((width, height))

  def recalc_drawable_and_hitbox(self, top_left: Vector2) -> Drawable:
    if not self.get_width_height():
      raise Exception('width height not calculated')

    # calculate drawable
    inf_surface = InfiniteSurface()
    button = self.get_button()
    inf_surface.blit(button, Vector2(0, 0))
    dropdown_content = self.dropdown_content.get() if self.show_dropdown.get() else None    
    if dropdown_content:
      blit_x = button.get_width() - dropdown_content.get_width_height()[0]
      blit_y = button.get_height() + self.gap.get()
      ret = dropdown_content.recalc_drawable_and_hitbox(top_left + Vector2(blit_x, blit_y))
      inf_surface.blit(ret.to_draw, Vector2(blit_x, blit_y))

    # recalculate hitbox
    button_rect = button.get_rect()
    button_rect.topleft = to_tuple(top_left)
    self.button_hitbox_.rect = button_rect
    
    d = inf_surface.get_drawable()
    self.set_drawable(d)
    return d

ChildAlignmentType = Literal['left', 'right', 'space_between']
class Container(UINode):
  def __init__(self,
               child_alignment: Param[ChildAlignmentType] = 'left',
               child_spacing: Param[int] = 10,
               direction: Param[Literal['row', 'col']] = 'row',
               
               children: Param[list[T3]] = [],
               padding: Param[int] = 10, 
               min_width: Param[int] = 0, 
               min_height: Param[int] = 0, 
               background_color: Param[AlphaColor] = (200, 200, 200, 255),
               id: str = 'none',
              ):
    super().__init__(children, padding, min_width, min_height, background_color, id)
    
    self.child_alignment = parse_param(child_alignment)
    self.child_spacing = parse_param(child_spacing)
    self.direction = parse_param(direction)
    
    self.container_hitbox_ = HitBox(
      self,
      Rect((-1, -1), (-1, -1))
    )
  
  def calc_width_height(self):
    # for c in self.children.get():
    #   c.calc_width_height()
    child_width_heights = [c.get_width_height() for c in self.children.get()]
    num_children = len(self.children.get())
    main_dir = 0 if self.direction.get() == 'row' else 1
    width_height = [0, 0]
    
    width_height[main_dir] = sum([c[main_dir] for c in child_width_heights]) + self.child_spacing.get() * max(num_children - 1, 0) + 2 * self.padding.get()
    width_height[1 - main_dir] = (max([c[1 - main_dir] for c in child_width_heights]) if len(child_width_heights) > 0 else 0) + 2 * self.padding.get()
    width_height[0] = max(width_height[0], self.min_width.get())
    width_height[1] = max(width_height[1], self.min_height.get())
    
    self.set_width_height(cast(tuple[int, int], tuple(width_height)))

  def recalc_drawable_and_hitbox(self, top_left: Vector2) -> Drawable:
    main_dir = 0 if self.direction.get() == 'row' else 1
    dirs = [Vector2(1, 0), Vector2(0, 1)]
    delta = [Vector2(-1, 1), Vector2(1, -1)]
    
    num_children = len(self.children.get())
    # need to get these before hand, else don't know how to space out the nodes
    background = Surface(self.get_width_height(), pygame.SRCALPHA)
    background.fill(self.background_color.get())
    pygame.draw.rect(background, (0, 0, 0), pygame.Rect((0, 0), self.get_width_height()), 2)
    
    inf_surface = InfiniteSurface()
    inf_surface.blit(background, Vector2(0, 0))
    
    if self.child_alignment.get() == 'left':
      cur_top_left = Vector2(self.padding.get(), self.padding.get())
      
      for child in self.children.get():
        ret = child.recalc_drawable_and_hitbox(cur_top_left + top_left)
        inf_surface.blit(ret.to_draw, cur_top_left + ret.blit_offset)
        cur_top_left += dirs[main_dir] * (child.get_width_height()[main_dir] + self.child_spacing.get())   
    
    elif self.child_alignment.get() == 'right':
      cur_pt = self.get_width_height()[main_dir] * dirs[main_dir] + delta[main_dir] * self.padding.get()
      
      for child in reversed(self.children.get()):
        cur_top_left = cur_pt - dirs[main_dir] * child.get_width_height()[main_dir]
        
        ret = child.recalc_drawable_and_hitbox(cur_top_left + top_left)
        inf_surface.blit(ret.to_draw, cur_top_left + ret.blit_offset)
        cur_pt -= dirs[main_dir] * (child.get_width_height()[main_dir] + self.child_spacing.get())
        
    elif self.child_alignment.get() == 'space_between':
      pure_length = sum([c.get_width_height()[main_dir] for c in self.children.get()]) + self.child_spacing.get() * (num_children - 1)

      space_left = self.get_width_height()[main_dir] - pure_length - 2*self.padding.get()
      cur_top_left = Vector2(self.padding.get(), self.padding.get()) + dirs[main_dir] * (space_left / 2)
      
      for child in self.children.get():
        ret = child.recalc_drawable_and_hitbox(cur_top_left + top_left)
        inf_surface.blit(ret.to_draw, cur_top_left + ret.blit_offset)
        cur_top_left += child.get_width_height()[main_dir] * dirs[main_dir] 

    # set hitbox
    self.container_hitbox_.rect = Rect((0, 0), self.get_width_height())
    self.container_hitbox_.rect.topleft = to_tuple(top_left)
    
    d = inf_surface.get_drawable()
    self.set_drawable(d)   
    return d

class MySurface(UINode):
  def __init__(self,    
               surface: Param[Surface],
               show_outline: Param[bool] = Controlled(lambda: False, free=True),
               on_click: Param[Callable[[MouseEvent], Any] | None] = None,
               
               children: Param[list[T3]] = [],
               padding: Param[int] = 0, 
               min_width: Param[int] = 0, 
               min_height: Param[int] = 0, 
               background_color: Param[AlphaColor] = (0, 0, 0, 0),
               id: str = 'none'
  ):
    super().__init__(children, padding, min_width, min_height, background_color, id)
    self.surface = parse_param(surface)
    self.show_outline = parse_param(show_outline)
    self.on_click = parse_param(on_click)
    
    def on_click_(mouse_event: MouseEvent):
      f = self.on_click.get()
      if f:
        f(mouse_event)
    
    self.hitbox_ = HitBox(
      self, 
      Rect((-1, -1), (-1, -1)),
      on_click=on_click_
    )
  
  def calc_width_height(self):
    surf = self.surface.get()
    self.set_width_height((surf.get_width(), surf.get_height()))
  
  def recalc_drawable_and_hitbox(self, top_left: Vector2) -> Drawable:
    orig_surf = self.surface.get()
    outlined_surf = orig_surf.copy()
    pygame.draw.rect(outlined_surf, (0, 255, 0, 255), pygame.Rect((0, 0), (outlined_surf.get_width(), outlined_surf.get_height())), 2)

    surf = outlined_surf if self.show_outline.get() else orig_surf
    d = Drawable(surf, Vector2(0, 0))
    
    # set hitbox
    self.hitbox_.rect = Rect((0, 0), self.get_width_height())
    self.hitbox_.rect.topleft = to_tuple(top_left)
    self.set_drawable(d)
    return d

class PositionedUINode:
  def __init__(self, node: UINode, dest_top_left: Vector2 | Callable[[UINode], Vector2]) -> None:
    self.node = node
    # self.node.calc_width_height()
    self.node.recalculate_drawable_and_hitbox(dest_top_left)
    self.dest_top_left = dest_top_left

  def draw(self, surface: Surface):
    dest_top_left = self.dest_top_left
    if isinstance(dest_top_left, Callable):
      dest_top_left = dest_top_left(self.node)
    
    drawable = self.node.get_drawable()
    surface.blit(drawable.to_draw, drawable.blit_offset + dest_top_left)

class UIEngine:
  def __init__(self, gsm: StateManager) -> None:
    self.state_changed_in_frame = False
    self.gsm = gsm
    self.gsm.add_subscriber(self)
    self.positioned_nodes: list[PositionedUINode] = []
    
    self.best = None
    self.all = None
  
  def handle_input(self, mouse_event: MouseEvent):
    # if state change detected
    # - clear the cache of every single 'Controlled' object
    self.state_changed_in_frame = self.gsm.has_notification(self)
    self.gsm.consume_notification(self)
    
    if self.state_changed_in_frame:
      for pn in self.positioned_nodes:
        pn.node.uncache_width_height()
        pn.node.clear_caches()
    
    # update state of UI elements
    # - calculate width height and hitboxes
    # - get newest drawable ready
    # (here, we can expect a lot of cache hits)
    for pn in self.positioned_nodes:
      # pn.node.calc_width_height()
      pn.node.recalculate_drawable_and_hitbox(pn.dest_top_left)
    
    # update hitboxes / process click events
    best = None
    for pn in self.positioned_nodes:
      best = pn.node.get_best_hitbox(mouse_event)
      if best:
        break

    self.best = best
    all_hitboxes = [h for p_node in self.positioned_nodes for h in p_node.node.get_all_hitboxes()]
    self.all = all_hitboxes
    
    for h in all_hitboxes:
      h.update(mouse_event, h == best) # change the state and stuff for next frame
    
    consumed = self.best != None
    return None if consumed else mouse_event

  def draw(self, surface: Surface):
    for p_node in self.positioned_nodes:
      p_node.draw(surface)
      
    # if self.all:
    #   for h in self.all:
    #       pygame.draw.rect(surface, (255, 0, 0), h.rect, 1)
    
    if self.best:
      pygame.draw.rect(surface, (0, 0, 255), self.best.rect, 2)
    
  def test(self):
    
    
    
    
    pass