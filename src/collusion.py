from dataclasses import dataclass
from pygame import Rect
from pygame.math import Vector2
from constants import COE
from helper import *
from classes import Polygon

@dataclass
class CollusionData:
  objA: Polygon
  objB: Polygon
  penetration_depth: float
  contact_points: list[Vector2]
  collusion_normal: Vector2 # this points towards objA
  
  def __str__(self) -> str:
    res = ""
    for at in self.__dict__:
      res += f"{at}: {str(self.__dict__[at])}\n"
    return res
      
def range_depth(r1: tuple[float, float], r2: tuple[float, float]):
  if r1[0] > r2[0]:
    r1, r2 = r2, r1
  return r1[1] - r2[0]
  

def collide(b1: Polygon, b2: Polygon, touch: bool = False) -> CollusionData | None:
  """
    get collusion data for two objects. Returns none if not colliding
    touch: adds a leeway instead of checking for strict collusions
  """
  
  def adjust_rect(rect: Rect, thres: int):
    """
      if thres > 0, we expand the rect, else contract it
    """
    thres -= 1
    return Rect((rect.topleft[0] + thres, rect.topleft[1] + thres), (rect.width - 2*thres, rect.height - 2*thres))
  
  THRES = -5
  r1 = b1.get_bounding_box_global()
  r2 = b2.get_bounding_box_global()
  if touch:
    r1 = adjust_rect(r1, THRES)
    r2 = adjust_rect(r2, THRES)
  
  if r1.colliderect(r2):
    points1 = b1.get_points_global()
    points2 = b2.get_points_global()
    L1 = len(points1)
    L2 = len(points2)
    
    polygons = [b1, b2]
    points = [points1, points2]
    # get the smallest penetration depth, and normal which gives this
    # normal: (n, polygon (0 or 1)), so we know which polygon the normal is from
    # normal[polgon][index]
    normals = [[Vector2(-1, -1) for _ in range(L1)], [Vector2(-1, -1) for _ in range(L2)]]
    for i in range(L1):
      normal = rot_90_c(points1[(i + 1) % L1] - points1[i]).normalize()
      normals[0][i] = normal
    for i in range(L2):
      normal = rot_90_c(points2[(i + 1) % L2] - points2[i]).normalize()
      normals[1][i] = normal
    
    min_i = (-1, -1)
    min_d = 1E15
    for p in range(2):
      for i in range(len(normals[p])):
        normal = normals[p][i]
        range1 = polygons[p].project_onto_normal(normal)
        range2 = polygons[1 - p].project_onto_normal(normal)
        
        # for any normal, we use the SAT,
        abs_depth = range_depth(range1, range2)
        
        # need abs_depth >= thres
        if touch:
          if abs_depth < THRES:
            # found a separating axis
            return None
        else:
          if abs_depth <= 0:
            return None
        # - collusion normals are defined by a point and a direction
        # - we need range1 to be to the left of range2, otherwise this normal is invalid
        # - otherwise, this is not a valid collusion normal
        if range1[0] >= range2[0]:
          continue
        
        normal_depth = range1[1] - range2[0]
        if normal_depth < min_d:
          min_d = normal_depth
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
    # print(min_i)

    (polyA, i) = min_i

    normal = normals[polyA][i]
    
    v0 = points[polyA][i]
    v1 = points[polyA][(i + 1) % len(points[polyA])]

    
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
    w0 = points[polyB][(w_idx - 1) % len(points[polyB])]
    w1 = points[polyB][(w_idx + 1) % len(points[polyB])]
    # w0 -> w
    # w1 -> w
    # see which is more perpendicular to the normal
    # let this be incident edge
    incident = (w0, w) if abs(Vector2.dot(normal, w - w0)) <= abs(Vector2.dot(normal, w - w1)) else (w1, w)
    
    # w0, w1 is the incident edge
    (w0, w1) = incident
    collusion_points = clip([w0, w1], direction, Vector2.dot(direction, v0)) # may return none
    collusion_points = clip(collusion_points, -direction, Vector2.dot(-direction, v1))
    collusion_points = clip(collusion_points, -normal, Vector2.dot(-normal, v0))
    
    rangeA = polygons[polyA].project_onto_normal(normal)
    rangeB = polygons[polyB].project_onto_normal(normal)
    
    # finalA is object receiving hit. This is the object on the right
    # finalB is the opposite object
    finalA = polyB if rangeA[0] < rangeB[0] else polyA
    finalB = 1 - finalA
    
    collusion_data = CollusionData(
      objA = polygons[finalA],
      objB = polygons[finalB],
      collusion_normal = normal, # need it to point towards bodyA by convention
      contact_points = collusion_points,
      penetration_depth = min_d,
    )
    return collusion_data
  else:
    return None

def recalculate_penetration(collusion_data: CollusionData):
  """
    without recalculating the collusion normal for the two objects involved, recalculate the penetration
  """
  b1 = collusion_data.objA
  b2 = collusion_data.objB
  normal = collusion_data.collusion_normal
  range1 = b1.project_onto_normal(normal)
  range2 = b2.project_onto_normal(normal)
  if range1[0] > range2[0]:
    range1, range2 = range2, range1
  d = range1[1] - range2[0]
  return d

def avg(points: list[Vector2]):
  return Vector2(sum(map(lambda p: p.x, points)) / len(points), sum(map(lambda p: p.y, points)) / len(points))

def resolve_penetration(collusion_data: CollusionData):
  objA = collusion_data.objA
  objB = collusion_data.objB
  M_A = objA.mass
  M_B = objB.mass
  normal = collusion_data.collusion_normal
  rangeA = objA.project_onto_normal(normal)
  rangeB = objB.project_onto_normal(normal)
  if rangeA[0] > rangeB[0]:
    rangeA, rangeB = rangeB, rangeA
  d = rangeA[1] - rangeB[0]
  # inpenetrable objects: mass is -1
  if M_A < 0:
    objB.center_of_mass += (-d) * normal
    return
  if M_B < 0:
    objA.center_of_mass += d * normal
    return
  objA.center_of_mass += (d * (M_B / (M_A + M_B))) * normal
  objB.center_of_mass += (-d * (M_A / (M_A + M_B))) * normal

def recalculate_separating_velocity(collusion_data: CollusionData):
  """
    gives the value of the separating velocity without changing anything
  """
  objA = collusion_data.objA
  objB = collusion_data.objB
  n = collusion_data.collusion_normal
  
  p = avg(collusion_data.contact_points)
  a = objA.center_of_mass
  b = objB.center_of_mass
  
  r_ap = p - a
  v_a = objA.linear_velocity
  wa = objA.rotational_velocity
  v_ap = v_a + wa * rot_90_ac(r_ap)
  
  r_bp = p - b
  v_b = objB.linear_velocity
  wb = objB.rotational_velocity
  v_bp = v_b + wb * rot_90_ac(r_bp)
  v_ab = v_ap - v_bp
  
  ans = v_ab.dot(n)
  return ans

def resolve_velocity(collusion_data: CollusionData, frame_length: float):
  
  objA = collusion_data.objA
  objB = collusion_data.objB
  n = collusion_data.collusion_normal
  p = avg(collusion_data.contact_points)
  M_A = objA.mass
  M_B = objB.mass
  I_A = objA.rotational_inertia
  I_B = objB.rotational_inertia

  a = objA.center_of_mass
  b = objB.center_of_mass
  
  r_ap = p - a
  v_a = objA.linear_velocity
  wa = objA.rotational_velocity
  r_ap_perp = rot_90_ac(r_ap)
  v_ap = v_a + wa * r_ap_perp
  
  r_bp = p - b
  v_b = objB.linear_velocity
  wb = objB.rotational_velocity
  r_bp_perp = rot_90_ac(r_bp)
  v_bp = v_b + wb * r_bp_perp
  v_ab = v_ap - v_bp
  
  invMA = 1 / M_A if M_A > 0 else 0
  invMB = 1 / M_B if M_B > 0 else 0
  rap_div_IA = ((r_ap_perp.dot(n) * r_ap_perp.dot(n)) / I_A) if M_A > 0 else 0
  rbp_div_IB = ((r_bp_perp.dot(n) * r_bp_perp.dot(n)) / I_B) if M_B > 0 else 0

  numerator = -(1 + COE) * v_ab.dot(n)
  
  denom = n.dot(n) * (invMA + invMB) + rap_div_IA + rbp_div_IB
  impulse = numerator / denom
  # don't change any velocities of the object if it has infinite mass
  # if object is moving too slowly, then we realize it is a resting contact
  # - don't affect the accelerations, so speed can still build up
  # - if speed <= frame_length * acceleration
  # - but acceleration = linear_acceleration + rotational_acceleration * r_ap
  # - need a way to remove the speed
  # - 
  
  if M_A > 0:
    objA.linear_velocity = v_a + (impulse / M_A) * n
    objA.rotational_velocity = wa + (r_ap_perp.dot(impulse * n)) / I_A
  
  if M_B > 0:
    objB.linear_velocity = v_b + (-impulse / M_B) * n
    objB.rotational_velocity = wb + (r_bp_perp.dot(-impulse * n)) / I_B
