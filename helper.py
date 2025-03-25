from pygame.math import Vector2



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

def rot_90_ac(vec: Vector2):
  """
    rotate a vector 90 degrees anticlockwise
  """
  return Vector2(-vec.y, vec.x)

def rot_90_c(vec: Vector2):
  """
    rotate a vector 90 degrees clockwise
  """
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

