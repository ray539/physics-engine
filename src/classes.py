import pygame
from pygame.math import Vector2
from pygame import Rect, Surface
from abc import ABC, abstractmethod
from collections.abc import Iterable
from common import avg
from common import draw_arrow, label
from constants import DELTA, DELTA_THETA, GRAVITY, RESTING_CONTACT_THRES
from helper import *
import math

from ui_lib2 import AlphaColor, lighten

class RigidBody(ABC):
  def __init__(self):
    super().__init__()
    self.mass: float = 0
    self.linear_velocity: Vector2 = Vector2(0, 0)
    self.linear_acceleration: Vector2 = Vector2(0, 0)

    self.rotational_inertia: float = 0
    self.rotational_acceleration: float = 0
    self.rotational_displacement: float = 0
    self.rotational_velocity: float = 0
    
  @abstractmethod
  def update_unconstrained(self, dt: float) -> None:
    pass

def negligible_difference(com1: Vector2 | None, com2: Vector2 | None, rot_dis_1: float | None, rot_dis_2: float | None):
  if com1 == None or com2 == None or rot_dis_1 == None or rot_dis_2 == None:
    return True # first frame, return true
  return Vector2.magnitude_squared(com1 - com2) <= DELTA and min(abs(rot_dis_1 - rot_dis_2), 2*math.pi - abs(rot_dis_1 - rot_dis_2)) <= DELTA_THETA

def might_be_stationary(b: 'Polygon'):
  return negligible_difference(b.center_of_mass, b.prev_center_of_mass, b.rotational_displacement, b.prev_rotational_displacement) \
       and negligible_difference(b.center_of_mass, b.begin_pos, b.rotational_displacement, b.begin_rot)

class Polygon(RigidBody):
  def __init__(self, points: Iterable[Vector2], body_id: int, immovable: bool = False):
    super().__init__()
    self.body_id = body_id
    self.area = area_of_polygon(list(points))
    self.mass = area_of_polygon(list(points)) if not immovable else -1
    self.rotational_inertia = moment_inertia_of_polygon(list(points)) if not immovable else -1
    # polygon
    # - center
    # - points relative to center
    self.center_of_mass: Vector2 = center_of_mass(list(points))
    self.points_local: list[Vector2] = list(map(lambda p: p - self.center_of_mass, points))
    
    # for resting contacts
    self.prev_center_of_mass: Vector2 | None = None
    self.prev_rotational_displacement: float | None = None
    self.current_run = 0
    self.begin_pos = Vector2(self.center_of_mass)
    self.begin_rot = self.rotational_displacement
    self.might_be_resting = False
    self.resting = immovable
    
    self.touching: set[Polygon] = set()
    # self.touching_prev: set[int] = set()
    
    
    # for drawing
    self.fill_color: AlphaColor = (255, 0, 0, 255) if self.mass > 0 else (0, 0, 255, 255)
    self.border_color: AlphaColor = lighten(self.fill_color, 30)
    self.border_thickness = 0
    self.draw_vel_vector = True
    
    # for on drag state
    self.is_being_dragged = False

  def draw(self, screen: Surface):
    screen_points = world_to_screen(self.get_points_global())
    mid = avg(screen_points)
    pygame.draw.polygon(screen, self.fill_color, screen_points)
    lab = label(str(self.body_id), 'Arial', 10)
    rect = pygame.Rect((0, 0), (lab.get_width(), lab.get_height()))
    rect.center = (int(mid.x), int(mid.y))
    screen.blit(lab, rect)
    if self.border_thickness > 0:
      pygame.draw.polygon(screen, self.border_color, screen_points, self.border_thickness)
    
    if self.draw_vel_vector:
      draw_arrow(self.center_of_mass, self.center_of_mass + self.linear_velocity, screen)
    
    

  def get_bounding_box_global(self):
    global_points = self.get_points_global()
    x_min = min(map(lambda p : p.x, global_points))
    y_min = min(map(lambda p : p.y, global_points))
    left_top = Vector2(x_min, y_min)
    
    x_max = max(map(lambda p : p.x, global_points))
    y_max = max(map(lambda p : p.y, global_points))
    width_height = Vector2(x_max - x_min, y_max - y_min)
    
    return Rect(left_top, width_height)
  
  def project_onto_normal(self, normal: Vector2):
    """
      ensure normal is normalized before passing in here
    """
    global_points = self.get_points_global()
    dists = list(map(lambda p: Vector2.dot(normal, p) , global_points))
    return (min(dists), max(dists))
  
  def get_points_global(self):
    return list(map(lambda p: p.rotate_rad(self.rotational_displacement) + self.center_of_mass, self.points_local))

  def stop_resting(self):
    if not self.resting:
      # don't want to reset current run (if it exists)
      return
    if self.mass < 0:
      return
    
    self.resting = False
    self.begin_pos = Vector2(self.center_of_mass)
    self.begin_rot = self.rotational_displacement
    self.current_run = 0

  def update_rest(self):
    if self.mass < 0:
      return
    # current body might be stationary
    # all bodies this body touches also might be stationary (confirmed not moving)
    if self.might_be_resting and len([b for b in self.touching if (not b.might_be_resting)]) == 0:
      self.current_run = min(self.current_run + 1, RESTING_CONTACT_THRES)
    else:
      self.resting = False
      self.current_run = 0
      self.begin_pos = Vector2(self.center_of_mass)

    if self.current_run >= RESTING_CONTACT_THRES:
      self.current_run = 0
      self.resting = True
      self.linear_velocity = Vector2(0, 0)
      self.rotational_velocity = 0

    self.prev_center_of_mass = Vector2(self.center_of_mass)
    self.prev_rotational_displacement = self.rotational_displacement

  def update_unconstrained(self, dt: float) -> None:
    if self.mass < 0:
      # immovable
      return
    if self.resting:
      return
    if self.is_being_dragged:
      return

    # forces will update the acceleration
    self.center_of_mass += self.linear_velocity * dt + (1/2) * dt * dt * self.linear_acceleration
    self.linear_velocity += self.linear_acceleration
    
    self.rotational_displacement += self.rotational_velocity * dt + (1/2) * dt * dt * self.rotational_acceleration
    self.rotational_displacement %= (2*math.pi)
    self.rotational_velocity += self.rotational_acceleration
    
  def apply_force(self, contact_point_world: Vector2, force_vector: Vector2) -> None:
    """
      contact_point_world: contact point in world coordinates
    """
    if self.mass < 0:
      return
    self.linear_acceleration += force_vector / self.mass
    
    d = contact_point_world - self.center_of_mass
    torque = Vector2.cross(d, force_vector)
    self.rotational_acceleration += torque / self.rotational_inertia
  
  def __str__(self):
      return f"{self.__class__.__name__}({self.__dict__})"
# ForceGenerator
# - eg. gravity
# - attatched to an object

# Force
# - applied force
# - contains (object, contact point, force_vector)
class ForceGenerator:
  def __init__(self) -> None:
    pass
  
  @abstractmethod
  def apply_forces(self) -> None:
    pass

class ConstantForceGenerator(ForceGenerator):
  def __init__(self, target: Polygon, force_vector: Vector2) -> None:
    """
      generate a constant force on a body attatched to center of mass
    """
    super().__init__()
    self.target = target
    self.force_vector = force_vector
  
  def apply_forces(self) -> None:
    self.target.apply_force(self.target.center_of_mass, self.force_vector)
  

class GravityForceGenerator(ForceGenerator):
  def __init__(self, world_bodies: list[Polygon]) -> None:
    """
      applies 'GRAVITY' to all objects
    """
    self.world_bodies = world_bodies
  
  def apply_forces(self):
    for body in self.world_bodies:
      body.apply_force(body.center_of_mass, Vector2(0, -GRAVITY))
      
class PullForceGenerator(ForceGenerator):
  def __init__(self, target: Polygon, contact_point_world: Vector2, destination: Vector2) -> None:
    """
      acting on a fixed point on the target, generate force towards the destination
    """
    self.target = target
    self.contact_point_local = contact_point_world - self.target.center_of_mass
    self.destination = destination
    
  def apply_forces(self) -> None:
    force_v = Vector2.normalize(self.destination - (self.target.center_of_mass + self.contact_point_local))
    self.target.apply_force(self.contact_point_local, force_v)
