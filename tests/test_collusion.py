import sys
import os
from typing import cast
# __file__: the location of the current file
# os.path.dirname: function which extracts directory of file
# os.path.join: function to join 2 string paths
root_dir = os.path.join(os.path.dirname(__file__), '../src')
sys.path.append(root_dir)
from pygame.math import Vector2
from classes import Polygon
from collusion import *
from engine import *
from helper import *
import pickle

def test_one_square_one_immovable():
  # test polygon rebounding against a square
  immovable = Polygon(get_square(Vector2(50, 0), 50), True)
  square_1 = Polygon(get_square(Vector2(5, 0), 50), 0)
  square_1.linear_velocity = Vector2(1000, 0)
  
  cd = cast(CollusionData, collide(immovable, square_1))
  print(cd)
  resolve_velocity(cd, 1/60)
  print(immovable)
  print(square_1)
  
def test1():
  f = open(f'{os.path.dirname(__file__)}/test1', 'rb')
  engine = cast(Engine, pickle.loads(f.read()))
  engine.update(1/60)
  
def test2():
  a = Polygon([
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(10, 10),
    Vector2(0, 10)
  ], 0)
  
  b = Polygon([
    Vector2(5, 13),
    Vector2(11, 7),
    Vector2(15, 11),
    Vector2(9, 17)
  ], 1)
  
def test3():
  a = Polygon([Vector2(50, 50), Vector2(450, 50), Vector2(450, 100), Vector2(50, 100)], True)
  b = Polygon([
    Vector2(430.068, 100), Vector2(480.068, 100.136), Vector2(479.932, 150.136), Vector2(429.932, 150)
  ], 0)
  
  print(a.get_points_global())
  print(a.linear_velocity)
  print()
  print(b.get_points_global())
  print(b.linear_velocity)
  
  cd = collide(a, b)
  print(cd)
  
def test4():
  a = Polygon([Vector2(50, 50), Vector2(450, 50), Vector2(450, 100), Vector2(50, 100)], 0)
  b = Polygon([Vector2(-2.411, 40.0692), Vector2(78.0902, 99.395), Vector2(18.7644, 179.896), Vector2(-61.7368, 120.57)], 1)
  
  cd = collide(a, b)
  print(cd)
  
def temp():
  a = Polygon([
    Vector2(50, 50),
    Vector2(450, 50),
    Vector2(450, 100),
    Vector2(50, 100)
  ], True)
  
  b = Polygon([
    Vector2(150, 150) + Vector2(0, -5),
    Vector2(200, 100) + Vector2(0, -5),
    Vector2(250, 150) + Vector2(0, -5),
    Vector2(200, 200) + Vector2(0, -5)
  ], 0)
  b.linear_velocity = Vector2(0, -1000)
  cd = collide(a, b)
  print(cd)
  
  
def test_thres_le_0():
  a = Polygon([
    Vector2(0, 0),
    Vector2(100, 0),
    Vector2(100, 100),
    Vector2(0, 100)
  ], 0)
  b = Polygon([
    Vector2(0, 0) + Vector2(100, 0),
    Vector2(100, 0) + Vector2(100, 0),
    Vector2(100, 100) + Vector2(100, 0),
    Vector2(0, 100) + Vector2(100, 0)
  ], 1)
  cd1 = collide(a, b)
  cd2 = collide(a, b, True)
  pass
  
if __name__ == '__main__':
  test_thres_le_0()