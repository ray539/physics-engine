from pygame.math import Vector2
from abc import ABC, abstractmethod
from collections.abc import Iterable

from constants import GRAVITY

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

def area_of_polygon(points: list[Vector2]) -> float:
  """
    assume points is labeled in AC order
  """
  area = 0
  N = len(points)
  for i in range(N):
    xi = points[i].x
    xi1 = points[(i + 1) % N].x
    yi = points[i].y
    yi1 = points[(i + 1) % N].y
    area += (yi + yi1) * (xi - xi1)
  area = area / 2
  return area

def moment_inertia_of_polygon(points: list[Vector2]) -> float:
  N = len(points)
  inertia = 0
  for i in range(N):
    xi = points[i].x
    xi1 = points[(i + 1) % N].x
    yi = points[i].y
    yi1 = points[(i + 1) % N].y
    inertia += (xi*yi1 - xi1*yi) * (xi1*xi1 + xi1*xi + xi*xi + yi1*yi1 + yi1*yi + yi*yi)
  inertia = inertia / 12
  return inertia

def center(points: list[Vector2]) -> Vector2:
  x_com = sum(map(lambda p: p.x, points))
  y_com = sum(map(lambda p: p.y, points)) / len(points)
  return Vector2(x_com, y_com)

def center_of_mass(points: list[Vector2]) -> Vector2:
  
  A = area_of_polygon(points)
  N = len(points)
  x_com = 0
  y_com = 0
  for i in range(N):
    xi = points[i].x
    xi1 = points[(i + 1) % N].x
    yi = points[i].y
    yi1 = points[(i + 1) % N].y
    x_com += (xi + xi1) * (xi * yi1 - xi1 * yi)
    y_com += (yi + yi1) * (xi * yi1 - xi1 * yi)
  x_com = x_com / (6*A)
  y_com = y_com / (6*A)
  return Vector2(x_com, y_com)



class Polygon(RigidBody):
  def __init__(self, points: Iterable[Vector2]):
    self.mass = area_of_polygon(list(points))
    self.rotational_inertia = moment_inertia_of_polygon(list(points))
    # polygon
    # - center
    # - points relative to center
    self.center_of_mass: Vector2 = center_of_mass(list(points))
    self.points_local: list[Vector2] = list(map(lambda p: p - self.center_of_mass, points))

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
    
    

    
class Engine:
  def __init__(self):
    self.force_generators: list[ForceGenerator] = [GravityForceGenerator(self.bodies)]
    self.bodies: list[Polygon] = []
  
  def apply_force(self, target: Polygon, contact_point_world: Vector2, force_vector: Vector2):
    target.apply_force(contact_point_world, force_vector)
    
  def update(self, dt: float):
    # apply forces
    for force_generator in self.force_generators:
      force_generator.apply_forces()    
    
    for body in self.bodies:
      body.update_unconstrained(dt)

