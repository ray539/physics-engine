from pygame.math import Vector2
from classes import *
from collusion import *
from constants import CONTACT_RESOLVER_MAX_ITERATIONS, VELOCITY_RESOLVER_MAX_ITERATIONS
  

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
    collusions: list[CollusionData] = []
    for i in range(len(self.bodies)):
      for j in range(i + 1, len(self.bodies)):
        tmp = collide(self.bodies[i], self.bodies[j])
        if tmp:
          collusions.append(tmp)
    
    # resolve velocity
    for _ in range(min(VELOCITY_RESOLVER_MAX_ITERATIONS, len(collusions) * 2)):
      mn_sep_val = 0.0 # want this to be negative, or else no objects are colliding
      min_idx = -1
      for i in range(len(collusions)):
        sep_val = recalculate_separating_velocity(collusions[i])
        if sep_val < mn_sep_val:
          mn_sep_val = sep_val
          min_idx = i
      if min_idx == -1 or mn_sep_val >= 0:
        break
      resolve_velocity(collusions[min_idx])
    
    
    # resolve interpenetration
    for _ in range(min(CONTACT_RESOLVER_MAX_ITERATIONS, len(collusions) * 2)):
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
