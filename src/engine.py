from copy import deepcopy
from typing import cast
from pygame.math import Vector2
from classes import *
from collusion import *
from common import Add, CircleInformation, Drag, ObjectInformation, PolygonInformation, State, StateManager, circle_graphic, get_polygon_surface, get_width_height, label, square_graphic, triangle_graphic
from constants import CONTACT_RESOLVER_MAX_ITERATIONS, SCREEN_WIDTH, VELOCITY_RESOLVER_MAX_ITERATIONS
from pygame import Surface
import pygame
import pickle
from ui_lib2 import HitBox, MouseEvent


def draw_polygon(polygon: Polygon, surface: Surface):
  if polygon.mass > 0:
    # if self.engine_polygon.resting:
    #   self.fill_color = (0, 255, 0)
    # else:
    fill_color = (255, 0, 0)
  else:
    fill_color = (0, 0, 255)
  border_color = tuple([200 if c == 0 else c for c in fill_color])
  border_thickness = 2
  
  screen_points = world_to_screen(polygon.get_points_global())
  mid = avg(screen_points)
  
  pygame.draw.polygon(surface, fill_color, screen_points)
  lab = label(str(polygon.body_id), 'Arial', 10)
  rect = pygame.Rect((0, 0), (lab.get_width(), lab.get_height()))
  rect.center = (int(mid.x), int(mid.y))
  surface.blit(lab, rect)

def draw_arrow(start: Vector2, end: Vector2, surface: pygame.Surface):
  pygame.draw.line(surface, (0, 0, 255), world_to_screen(start), world_to_screen(end), 2)
  # start -> end
  lv = end - start
  perp = rot_90_c(lv) * 0.1
  o = start + lv * 0.9
  a = o + perp
  c = o - perp
  pygame.draw.polygon(surface, (0, 0, 255), world_to_screen([a, end, c]))

def info_to_graphic(obj_info: ObjectInformation, color: tuple[int, int, int, int]):
  if isinstance(obj_info, PolygonInformation):
    # draw full scale object
    local_points = obj_info.local_points
    surf = get_polygon_surface(local_points, color)
    return surf
  elif isinstance(obj_info, CircleInformation):
    return circle_graphic(100, color)
  return Surface((0, 0))

class Thing:
  def __init__(self, obj_info: ObjectInformation, color: tuple[int, int, int], center_pos: Vector2) -> None:
    self.obj_info = obj_info
    self.light = True
    self.color = color
    self.center_pos = center_pos
    
  
  def get_drawable(self):
    res_color = (self.color[0], self.color[1], self.color[2], 100 if self.light else 255)
    surf = info_to_graphic(self.obj_info, res_color)
    w, h = surf.get_width(), surf.get_height()
    top_left = self.center_pos + Vector2(- w / 2, h / 2)
    return Drawable(surf, top_left)
  
  def get_global_points(self) -> list[Vector2]:
    """
      if thing is a polygon, get global points in world coordinates
    """
    # local_points
    if isinstance(self.obj_info, PolygonInformation):
      w, h = get_width_height(self.obj_info.local_points)
      top_left = self.center_pos + Vector2(- w / 2, h / 2)
      return [p + top_left for p in self.obj_info.local_points]
    return []

# for add
# object == 'triangle', 'circle', 'square'
# - we only have one hitbox, the screen itself
# - enter: show the slightly transparent selected shape
# - leave: delete transparent marker
# - press: make marker less transparent
# - release: make marker transparent

@dataclass
class Drawable:
  to_draw: Surface
  top_left: Vector2

class StateInstance(ABC):
  @abstractmethod
  def handle_input(self, mouse_event: MouseEvent):
    """
      handle mouse event
    """

class EmptyStateInstance(StateInstance):
  
  def __init__(self) -> None:
    super().__init__()
  
  def handle_input(self, mouse_event: MouseEvent):
    return

class AddStateInstance(StateInstance):
  def __init__(self, add_state: Add, engine: 'Engine', mouse_pos: Vector2) -> None:
    # initialize hitboxes
    
    l = [o for o in add_state.avaliable_objects if o.id == add_state.selected_id]
    obj = l[0] if len(l) > 0 else None
    
    self.thing: Thing | None = Thing(obj, (255, 0, 0), mouse_pos) if obj else None
    self.engine = engine
    
    def on_mouseenter(mouse_event: MouseEvent):
      pos = mouse_event.position
      self.thing = Thing(obj, (255, 0, 0), mouse_pos) if obj else None
    
    def on_mouseleave(mouse_event: MouseEvent):
      self.thing = None
    
    def on_mousepress(mouse_event: MouseEvent):
      if self.thing:
        self.thing.light = False
    
    def on_mouserelease(mouse_event: MouseEvent):
      if self.thing:
        self.thing.light = True
    
    def on_click(mouse_event: MouseEvent):
      pos = mouse_event.position
      if isinstance(obj, PolygonInformation):
        if self.thing:
          points = self.thing.get_global_points()
          self.engine.add_polygonal_body(points, False)
    
    self.screen_hitbox = HitBox(
      self,
      pygame.Rect((0, 0), (SCREEN_WIDTH, SCREEN_HEIGHT)),
      on_mouseenter=on_mouseenter,
      on_mouseleave=on_mouseleave,
      on_mousepress=on_mousepress,
      on_mouserelease=on_mouserelease,
      on_click=on_click
    )
  
  def handle_input(self, mouse_event: MouseEvent):
    # remember to update the engine's draw function here
    if self.thing:
      self.thing.center_pos = mouse_event.position

    self.screen_hitbox.update(mouse_event, self.screen_hitbox.rect.collidepoint(mouse_event.position))
    
    if self.thing:
      self.engine.extra_to_draw_frame = [self.thing.get_drawable()]
    else:
      self.engine.extra_to_draw_frame = []


def get_new_state_instance_from_global(global_state: StateManager, engine: 'Engine', mouse_pos: Vector2):
  if isinstance(global_state.current_state, Add):
    return AddStateInstance(global_state.current_state, engine, mouse_pos)
  return EmptyStateInstance()


def worldify_mouse_event(mouse_event: MouseEvent | None):
  """
    given a mouse event in screen coordinates \n
    return new mouse event in world coordinates
  """
  if mouse_event:
    mouse_event2 = deepcopy(mouse_event)
    mouse_event2.position = screen_to_world(mouse_event.position)
  else:
    mouse_event2 = MouseEvent(Vector2(-100, -100), 'none')
  return mouse_event2

class Engine:
  def __init__(self, global_state_manager: StateManager):
    self.bodies: list[Polygon] = []
    self.timer = 0
    self.id_gen = 0

    self.global_state_manager = global_state_manager
    self.global_state_manager.add_subscriber(self)
    
    self.instance_state: StateInstance = get_new_state_instance_from_global(global_state_manager, self, Vector2(-1, -1))
    self.extra_to_draw_frame: list[Drawable] = []
    
    self.pressed = False
    self.mouse_over = False
    
  def remove_movable_bodies(self):
    self.bodies = [b for b in self.bodies if b.mass < 0]
    self.id_gen = len(self.bodies)
  
  def add_polygonal_body(self, points: list[Vector2], immovable: bool = False):
    """
      points: world coordinates\n
      immovable: self explanatory\n
      returns the polygonal body created
    """
    new_body = Polygon(points, self.id_gen, immovable)
    self.id_gen += 1
    self.bodies.append(new_body)
    return new_body
  
  def apply_force(self, target: Polygon, contact_point_world: Vector2, force_vector: Vector2):
    target.apply_force(contact_point_world, force_vector)
  
  def resolve_collusions_simple(self, dt: float):
    """
      resolve collusions, NOT taking into account new collusions which are created
    """
    # check for collusions
    collusions: list[CollusionData] = []
    for i in range(len(self.bodies)):
      for j in range(i + 1, len(self.bodies)):
        tmp = collide(self.bodies[i], self.bodies[j])
        if tmp:
          collusions.append(tmp)
  
    # debug
    # - collusions before any resolution
    ret = deepcopy(collusions)
    
    # resolve velocities
    for _ in range(max(VELOCITY_RESOLVER_MAX_ITERATIONS, 2*len(collusions))):
      mn_sep_val = 0.0 # want this to be negative, or else no objects are colliding
      min_idx = -1
      for i in range(len(collusions)):
        sep_val = recalculate_separating_velocity(collusions[i])
        if sep_val < mn_sep_val:
          mn_sep_val = sep_val
          min_idx = i
      if min_idx == -1 or mn_sep_val >= 0:
        break
      resolve_velocity(collusions[min_idx], dt)

    # resolve interpenetration
    num_iters = 0
    for _ in range(max(CONTACT_RESOLVER_MAX_ITERATIONS, 2*len(collusions))):
      num_iters += 1
      mx_penetration = 0.0 # want this to be positive, else no penetrations
      max_idx = -1
      for i in range(len(collusions)):
        penetration = recalculate_penetration(collusions[i])
        if penetration > mx_penetration:
          mx_penetration = penetration
          max_idx = i
      if max_idx == -1 or mx_penetration <= 0:
        break
      resolve_penetration(collusions[max_idx])
    return ret
  
  def resolve_collusions_advanced(self, num_iters: int, dt: float):
    """
      repeat num_iters times:
      - delect collusions
      - resolve collusions
    """
    for _ in range(num_iters):
      collusions: list[CollusionData] = []
      for i in range(len(self.bodies)):
        for j in range(i + 1, len(self.bodies)):
          tmp = collide(self.bodies[i], self.bodies[j])
          if tmp:
            collusions.append(tmp)
      if len(collusions) == 0:
        break
      
      for col in collusions:
        if len(col.contact_points) > 0:
          resolve_velocity(col, dt)
          resolve_penetration(col) 
  
  def draw(self, surface: Surface):
    for b in self.bodies:
      draw_polygon(b, surface)
      draw_arrow(b.center_of_mass, b.center_of_mass + b.linear_velocity, surface)
      
    for d in self.extra_to_draw_frame:
      surface.blit(d.to_draw, world_to_screen(d.top_left))
  
  def handle_input(self, mouse_event: MouseEvent | None):
    # similar to the ui module
    # we need to get the best hitbox
    # hitbox:
    # - enter
    # - leave
    # - press
    # - click
    # but, different states have different hitboxes
    # for add
    # - we only have one hitbox, the screen itself
    # - enter: show the slightly transparent selected shape
    # - leave: delete transparent marker
    # - press: make marker less transparent
    # - release: make marker transparent
    # for drag
    # - all polygons have hitboxes
    # - on hover, make it slightly lighter
    # - on press, start drag motion
    # - on release ...
    # for delete
    # - screen no hitbox, but each polygon has it's own hitbox
    # - on click, the object gets deleted
    mouse_event = worldify_mouse_event(mouse_event)
    if self.global_state_manager.has_notification(self):
      self.instance_state = get_new_state_instance_from_global(self.global_state_manager, self, mouse_event.position)
      self.global_state_manager.consume_notification(self)


    self.instance_state.handle_input(mouse_event)
  
  def update(self, dt: float):
    # delete all forces
    for b in self.bodies:
      b.linear_acceleration = Vector2(0, 0)

    # apply gravity
    for b in self.bodies:
      b.apply_force(b.center_of_mass, Vector2(0, -GRAVITY * b.mass))
    
    # free body update
    for body in self.bodies:
      body.update_unconstrained(dt)
      
    # resolve collusions
    self.resolve_collusions_advanced(10, dt)

    # get neighbours of each body
    for b in self.bodies:
      b.touching.clear()
    for i in range(len(self.bodies)):
      for j in range(i + 1, len(self.bodies)):
        c = collide(self.bodies[i], self.bodies[j], True) # negative so get everything in vicinity
        if c != None:
          self.bodies[i].touching.add(self.bodies[j])
          self.bodies[j].touching.add(self.bodies[i])

    # mark potential bodies as resting
    for b in self.bodies:
      b.might_be_resting = might_be_stationary(b)

    for b in self.bodies:
      b.update_rest()
    
    return cast(list[CollusionData], [])