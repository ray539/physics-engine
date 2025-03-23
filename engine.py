from dataclasses import dataclass
from pygame.math import Vector2
from pygame import Rect
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

def rot_90_ac(vec: Vector2):
  return Vector2(-vec.y, vec.x)

def rot_90_c(vec: Vector2):
  return Vector2(vec.y, -vec.x)



def clip(points: list[Vector2], n: Vector2, o: float):
  """
    assume len(points) <= 2\n
    draws line between the points given
    ensure all points are >= 'o' when projected on n \n
    assumes n is unit vector
  """  
  
  if len(points) == 0:
    res: list[Vector2] = []
    return res
  
  v1 = points[0]
  v2 = points[1] if len(points) >= 2 else v1
  
  res: list[Vector2] = []
  d1 = n.dot(v1) - o
  d2 = n.dot(v2) - o
  
  # add valid points
  if d1 >= 0:
    res.append(v1)
  if d2 >= 0:
    res.append(v2)
  
  if d1 * d2 < 0:
    # they are on opposite sides, so there is one valid point so far
    e = v2 - v1
    u = d1 / (d1 + d2)
    v3 = v1 + u*e
    res.append(v3)
  return res

@dataclass
class CollusionData:
  objA: Polygon
  objB: Polygon
  penetration_depth: float
  contact_points: list[Vector2]  
  separating_velocity: float

# check if two points collide
# - if so, return collusion data
def collide(b1: Polygon, b2: Polygon):
  if b1.get_bounding_box_global().colliderect(b2.get_bounding_box_global()):
    points1 = b1.get_points_global()
    points2 = b2.get_points_global()
    L1 = len(points1)
    L2 = len(points2)
    
    points = [points1, points2]
    # get the smallest penetration depth, and normal which gives this
    # normal: (n, polygon (0 or 1)), so we know which polygon the normal is from
    
    # normal[polgon][index]
    normals = [[Vector2(-1, -1) for _ in range(L1)], [Vector2(-1, -1) for _ in range(L2)]]
    for i in range(L1):
      normal = rot_90_c(points1[(i + 1) % L1] - points1[i]).normalize()
      normals[0][i] = normal
    for i in range(L2):
      normal = rot_90_c(points1[(i + 1) % L2] - points1[i]).normalize()
      normals[1][i] = normal
    
    min_i = (-1, -1)
    min_d = 1E15
    for p in range(2):
      for i in range(len(normals[p])):
        normal = normals[p][i]
        range1 = b1.project_onto_normal(normal)
        range2 = b2.project_onto_normal(normal)
        if range1[0] > range2[0]:
          range1, range2 = range2, range1
        
        d = range1[1] - range2[0]
        if d <= 0:
          # found a separating axis
          return None
        if d < min_d:
          min_d = d
          min_i = (p, i)
    
    # resolving interpenetration
    # - move b1 in direction 'n' a distance of m2/(m1 + m2)
    # - move b2 in direction 'n' a distance of m1/(m1 + m2)
    
    # for normal in minimum direction
    #   A = polygon
    #   B = not polygon
    #   find v, point in B which is furthest along normal
    #   find v0 -> v,  v1 -> v, and decide which one is more perpendicular to n (say its v0 -> v)
    #   this is the incident edge
    #   clip v0 -> v along normal
    (polyA, i) = min_i
    normal = normals[polyA][i]
    v0 = points[polyA][i]
    v1 = points[polyA][(i + 1) % L1]
    direction = (v1 - v0).normalize()
    # (v0, v1) is the reference edge
    
    polyB = 1 - polyA
    w_dist = 1E15
    w_idx = -1
    for i in range(len(points[polyB])):
      d = Vector2.dot(points[polyB][i], normal)
      if d < w_dist:
        w_dist = d
        w_idx = i
    
    w = points[polyB][w_idx]
    w0 = points[polyB][(w_idx - 1) % L2]
    w1 = points[polyB][(w_idx + 1) % L2]
    
    # w0 -> w
    # w1 -> w
    # see which is more perpendicular to the normal
    # let this be incident edge
    incident = (w0, w) if abs(Vector2.dot(normal, w - w0)) <= abs(Vector2.dot(normal, w - w1)) else (w1, w)
    
    # w0, w1 is the incident edge
    (w0, w1) = incident
    collusion_points = clip([w0, w1], direction, Vector2.dot(direction, v0))
    collusion_points = clip(collusion_points, -direction, Vector2.dot(-direction, v1))
    collusion_points = clip(collusion_points, -normal, Vector2.dot(-normal, v0))
    
    
  else:
    return None

  
  

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
    
    # free body update
    for body in self.bodies:
      body.update_unconstrained(dt)
    
    # check for collusions
    
