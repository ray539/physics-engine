from pygame.math import Vector2
from pygame import Rect
from abc import ABC, abstractmethod
from collections.abc import Iterable
from constants import GRAVITY
from helper import *

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
  
class Polygon(RigidBody):
  def __init__(self, points: Iterable[Vector2]):
    self.mass = area_of_polygon(list(points))
    self.rotational_inertia = moment_inertia_of_polygon(list(points))
    # polygon
    # - center
    # - points relative to center
    self.center_of_mass: Vector2 = center_of_mass(list(points))
    self.points_local: list[Vector2] = list(map(lambda p: p - self.center_of_mass, points))

  def get_bounding_box_global(self):
    x_min = min(map(lambda p : p.x, self.points_local))
    y_min = min(map(lambda p : p.y, self.points_local))
    p1 = Vector2(x_min, y_min) + self.center_of_mass
    
    x_max = max(map(lambda p : p.x, self.points_local))
    y_max = max(map(lambda p : p.y, self.points_local))
    p2 = Vector2(x_max, y_max) + self.center_of_mass
    
    return Rect(p1, p2)
  
  def project_onto_normal(self, normal: Vector2):
    """
      ensure normal is normalized before passing in here
    """
    global_points = self.get_points_global()
    dists = list(map(lambda p: Vector2.dot(normal, p) , global_points))
    return (min(dists), max(dists))
  
  def get_points_global(self):
    return list(map(lambda p: p + self.center_of_mass, self.points_local))

  def update_unconstrained(self, dt: float) -> None:
    if self.mass < 0:
      # immovable
      return
    # forces will update the acceleration
    self.center_of_mass += self.linear_velocity * dt + (1/2) * dt * dt * self.linear_acceleration
    self.linear_velocity += self.linear_acceleration
    
    self.rotational_displacement += self.rotational_velocity * dt + (1/2) * dt * dt * self.rotational_acceleration
    self.rotational_velocity += self.rotational_acceleration
      
  def apply_force(self, contact_point_world: Vector2, force_vector: Vector2) -> None:
    """
      contact_point_world: contact point in world coordinates
    """
    self.linear_acceleration += force_vector / self.mass
    
    d = contact_point_world - self.center_of_mass
    torque = Vector2.cross(d, force_vector)
    self.rotational_acceleration += torque / self.rotational_inertia
    
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