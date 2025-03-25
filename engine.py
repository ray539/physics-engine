from pygame.math import Vector2
from classes import *
from collusion import *

  

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
    
    # resolve collusions
    # - first, resolve all velocities
    #   - get collusion with most negative separating velocity
    # - then resolve all interpenetrations
    #   - get collusion with largest interpenetration
    #   - resolve it
    #   - note, after resolving penetration, we don't bother recalculating the normals

    
    