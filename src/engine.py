from copy import deepcopy
from typing import cast
from pygame.math import Vector2
from classes import *
from collusion import *
from constants import CONTACT_RESOLVER_MAX_ITERATIONS, VELOCITY_RESOLVER_MAX_ITERATIONS
from pygame import Surface
import pygame
import pickle

from input import MouseEvent

class Engine:
  def __init__(self):
    self.bodies: list[Polygon] = []
    self.timer = 0
    self.id_gen = 0
  
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
  
  def preupdate(self, mouse_event: MouseEvent):
    for type in mouse_event.types:
      pos = screen_to_world(mouse_event.position)
      if type == 'click':
        d = 50
        points: list[Vector2] = [
            Vector2(-d,  -d) + pos,
            Vector2(d,  -d) + pos,
            Vector2(0, d) +pos,
        ]
        self.add_polygonal_body(points)
        
            
    
  
  def update(self, dt: float):
    
    # handle clicks here?
    
    
    
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