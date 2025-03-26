from dataclasses import dataclass
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

# check if two points collide
# - if so, return collusion data
def collide(b1: Polygon, b2: Polygon) -> CollusionData | None:
  if b1.get_bounding_box_global().colliderect(b2.get_bounding_box_global()):
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
    
    collusion_data = CollusionData(
      objA = polygons[polyA],
      objB = polygons[polyB],
      collusion_normal = -normal, # need it to point towards bodyA by convention
      contact_points= collusion_points,
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
  objA.center_of_mass += (d * M_B / (M_A + M_B)) * normal
  objB.center_of_mass += (-d * M_A / (M_A + M_B)) * normal

def recalculate_separating_velocity(collusion_data: CollusionData):
  objA = collusion_data.objA
  objB = collusion_data.objB
  p = avg(collusion_data.contact_points)
  a = objA.center_of_mass
  b = objB.center_of_mass
  r_ap = p - a
  n = collusion_data.collusion_normal
  v_a = collusion_data.objA.linear_velocity
  wa = collusion_data.objA.rotational_velocity
  v_ap = v_a + wa * rot_90_ac(r_ap)
  r_bp = p - b
  v_b = collusion_data.objB.linear_velocity
  wb = collusion_data.objB.rotational_velocity
  v_bp = v_b + wb * rot_90_ac(r_bp)
  v_ab = v_ap - v_bp
  return v_ab.dot(n)

def resolve_velocity(collusion_data: CollusionData):
  objA = collusion_data.objA
  objB = collusion_data.objB
  
  M_A = objA.mass
  M_B = objB.mass
  I_A = objA.rotational_inertia
  I_B = objB.rotational_inertia
  
  p = avg(collusion_data.contact_points)
  a = objA.center_of_mass
  b = objB.center_of_mass
  
  r_ap = p - a
  n = collusion_data.collusion_normal
  v_a = collusion_data.objA.linear_velocity
  wa = collusion_data.objA.rotational_velocity
  r_ap_perp = rot_90_ac(r_ap)
  v_ap = v_a + wa * r_ap_perp
  
  r_bp = p - b
  v_b = collusion_data.objB.linear_velocity
  wb = collusion_data.objB.rotational_velocity
  r_bp_perp = rot_90_ac(r_bp)
  v_bp = v_b + wb * r_bp_perp
  v_ab = v_ap - v_bp
  
  numerator = -(1 + COE) * v_ab.dot(n)
  denom = n.dot(n) * (1 / M_A + 1 / M_B) + (r_ap_perp.dot(n) * r_ap_perp.dot(n)) / I_A + (r_bp_perp.dot(n) * r_bp_perp.dot(n)) / I_B
  impulse = numerator / denom
  
  objA.linear_velocity = v_a + (impulse / M_A) * n
  objA.rotational_velocity = wa + (r_ap_perp.dot(impulse * n)) / I_A
  
  objB.linear_velocity = v_b + (-impulse / M_A) * n
  objB.rotational_velocity = wb + (r_ap_perp.dot(-impulse * n)) / I_B
