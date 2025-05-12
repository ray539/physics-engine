import sys
import os
# __file__: the location of the current file
# os.path.dirname: function which extracts directory of file
# os.path.join: function to join 2 string paths
root_dir = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(root_dir)
from src.helper import area_of_polygon, center_of_mass, moment_inertia_of_polygon, clip
from pygame.math import Vector2
from math import isclose

def vector_isclose(rec: Vector2, exp: Vector2, abs_tol: float = 1e-3):
  return isclose(rec.x - exp.x, 0, abs_tol=abs_tol) and isclose(rec.y - exp.y, 0, abs_tol=abs_tol)
  
def vector_list_isclose(rec: list[Vector2], exp: list[Vector2], abs_tol: float = 1e-3):
  rec.sort(key = lambda p: (p.x, p.y))
  exp.sort(key = lambda p: (p.x, p.y))
  if len(rec) != len(exp):
    return False
  for i in range(len(rec)):
    if not vector_isclose(rec[i], exp[i], abs_tol):
      return False
  return True
  
def test_area_of_polygon():
  # triangle
  assert area_of_polygon([Vector2(0, 0), Vector2(1, 0), Vector2(1,1)]) == 0.5
  # Square (1x1)
  assert area_of_polygon([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)]) == 1.0

  # Rectangle (2x1)
  assert area_of_polygon([Vector2(0, 0), Vector2(2, 0), Vector2(2, 1), Vector2(0, 1)]) == 2.0

  # Parallelogram
  assert area_of_polygon([Vector2(0, 0), Vector2(2, 0), Vector2(3, 1), Vector2(1, 1)]) == 2.0

def test_center_of_mass():
  

  # **Triangle (Base = 2, Height = 2)**
  # Centroid of a triangle with vertices at (0, 0), (2, 0), and (1, 2) is at (1, 2/3)
  triangle_points = [
      Vector2(0, 0),
      Vector2(2, 0),
      Vector2(1, 2)
  ]
  centroid = center_of_mass(triangle_points)
  assert isclose(centroid.x, 1.0, abs_tol=1e-3)
  assert isclose(centroid.y, 2 / 3, abs_tol=1e-3)

  # **Square (Side = 1, Centered at Origin)**
  # Centroid of a square centered at the origin is (0, 0)
  square_points = [
      Vector2(-0.5, -0.5),
      Vector2(0.5, -0.5),
      Vector2(0.5, 0.5),
      Vector2(-0.5, 0.5)
  ]
  centroid = center_of_mass(square_points)
  assert isclose(centroid.x, 0.0, abs_tol=1e-3)
  assert isclose(centroid.y, 0.0, abs_tol=1e-3)

  # **Rectangle (Width = 2, Height = 1)**
  # Centroid of a rectangle (width=2, height=1) centered at the origin should be (0, 0)
  rectangle_points = [
      Vector2(-1, -0.5),
      Vector2(1, -0.5),
      Vector2(1, 0.5),
      Vector2(-1, 0.5)
  ]
  centroid = center_of_mass(rectangle_points)
  assert isclose(centroid.x, 0.0, abs_tol=1e-3)
  assert isclose(centroid.y, 0.0, abs_tol=1e-3)

  # **Irregular Polygon (Pentagon Approximation)**
  # A pentagon with arbitrary points (Approximated centroid should be near the center)
  pentagon_points = [
      Vector2(0, 1),
      Vector2(-0.951, 0.309),
      Vector2(-0.588, -0.809),
      Vector2(0.588, -0.809),
      Vector2(0.951, 0.309)
  ]
  centroid = center_of_mass(pentagon_points)
  # Expecting the centroid to be near the center (around (0, 0))
  print(centroid)
  assert isclose(centroid.x, 0.0, abs_tol=1e-2)
  assert isclose(centroid.y, 0.0, abs_tol=1e-2)

def test_moment_of_inertia_of_polygon():
    
    square_points = [
        Vector2(-1, -1),
        Vector2(1, -1),
        Vector2(1, 1),
        Vector2(-1, 1)
    ]
    expected_inertia_square = 16 / 6
    inertia = moment_inertia_of_polygon(square_points)
    assert isclose(inertia, expected_inertia_square, abs_tol=1e-4), f"Failed for Square: {inertia}"
    
    offset = Vector2(69, 69)
    square_points_uncentered = [
        Vector2(-1, -1) + offset,
        Vector2(1, -1) + offset,
        Vector2(1, 1) + offset,
        Vector2(-1, 1) + offset
    ]
    inertia = moment_inertia_of_polygon(square_points)
    assert isclose(inertia, expected_inertia_square, abs_tol=1e-4), f"Failed for Square uncentered: {inertia}"

    rectangle_points = [
        Vector2(-1, -2),
        Vector2(1, -2),
        Vector2(1, 2),
        Vector2(-1, 2)
    ]
    expected_inertia_rectangle = 13.3333
    inertia = moment_inertia_of_polygon(rectangle_points)
    assert isclose(inertia, expected_inertia_rectangle, abs_tol=1e-4), f"Failed for Rectangle: {inertia}"

    
    # 🔹 **Irregular Polygon (Pentagon Approximation)**
    # Test with a simple irregular polygon, the inertia would be calculated but may not have an exact value
    pentagon_points = [
        Vector2(0, 1),
        Vector2(-0.951, 0.309),
        Vector2(-0.588, -0.809),
        Vector2(0.588, -0.809),
        Vector2(0.951, 0.309)
    ]
    # Since we do not have an exact theoretical value, we simply test that inertia is calculated
    inertia = moment_inertia_of_polygon(pentagon_points)
    assert inertia > 0, f"Failed for Pentagon: {inertia}"

def test_clip():
  points = [Vector2(0, 1), Vector2(3, 2)]
  n = Vector2(1, 0)
  o = 1
  res = clip(points, n, o)
  exp = [Vector2(1, 4/3), Vector2(3, 2)]
  assert vector_list_isclose(res, exp, 1e-3)
  
  points = [Vector2(3, 2)]
  res = clip(points, n, 2)
  exp = [Vector2(3, 2), Vector2(3, 2)]
  assert vector_list_isclose(res, exp, 1e-3)
  
  points = [Vector2(0, 1), Vector2(3, 2)]
  res = clip(points, n, 3)
  exp = [Vector2(3, 2)]
  assert vector_list_isclose(res, exp, 1e-3)



