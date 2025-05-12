import pickle
from typing import cast
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from collusion import CollusionData, collide
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from classes import Polygon as engine_Polygon
from engine import Engine
from helper import get_square, rot_90_c, screen_to_world, world_to_screen
from copy import deepcopy

class Polygon:
  def __init__(self, engine_polygon: engine_Polygon) -> None:
    """
      wrapper around engine polygon, including methods to draw
      points: global (word) coordinates
    """
    self.engine_polygon = engine_polygon
    self.fill_color = (0, 0, 255) if self.engine_polygon.mass < 0 else (255, 0, 0)
    self.border_color = (200, 200, 255) if self.engine_polygon.mass < 0 else (255, 200, 200)
    self.is_being_dragged = False

  def draw(self, surface: Surface):
    screen_points = world_to_screen(self.engine_polygon.get_points_global())
    thickness = 5
    pygame.draw.polygon(surface, self.fill_color, screen_points)
    pygame.draw.polygon(surface, self.border_color, screen_points, thickness)

def draw_arrow(start: Vector2, end: Vector2, surface: pygame.Surface):
  pygame.draw.line(surface, (0, 0, 255), world_to_screen(start), world_to_screen(end), 2)
  # start -> end
  lv = end - start
  perp = rot_90_c(lv) * 0.1
  o = start + lv * 0.9
  a = o + perp
  c = o - perp
  pygame.draw.polygon(surface, (0, 0, 255), world_to_screen([a, end, c]))

# each object has a 'click' event handler
# this is how we will interact with the objects 
class Controller:
  def __init__(self) -> None:
    pygame.init()
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = False
    self.engine = Engine()
    
    self.engine.add_polygonal_body(
      [
          Vector2(50, 50),
          Vector2(SCREEN_WIDTH - 50, 50),
          Vector2(SCREEN_WIDTH - 50, 100),
          Vector2(50, 100)
        ], 
      True
    )
    
    self.engine.add_polygonal_body(
      [
          Vector2(0, 0) + Vector2(-10, 100),
          Vector2(100, 0) + Vector2(-10, 100),
          Vector2(100, 100) + Vector2(-10, 100),
          Vector2(0, 100) + Vector2(-10, 100),
      ], 
      False
    )
        
    # for detecting clicks
    self.mouse_down = False
    self.selected_object: Polygon | None = None
  
  def debug_mode(self):
    self.running = True
    
    saves: list[Engine] = [self.engine]
    idx = 0 # points to current state
    cd: CollusionData | None = None
    
    def inc_index():
      nonlocal idx
      nonlocal cd
      idx += 1
      print(f'go forward to state {idx}')
      new_engine = deepcopy(self.engine)
      cols = new_engine.update(1/60) # get new state from latest
      if idx == len(saves):
        saves.append(new_engine)
      else:
        saves[idx] = new_engine
      self.engine = saves[idx]
      print(f'state {idx}')
      for b in self.engine.bodies:
        print(b.get_points_global())
        print(b.linear_velocity)
        print(b.rotational_velocity)
        print()
      cd = cols[0] if len(cols) > 0 else None
    
    def dec_index():
      nonlocal idx
      nonlocal cd
      idx = max(0, idx - 1)
      print(f'go back to state {idx}')
      self.engine = saves[idx]
      print(f'state: {idx}')
      for b in self.engine.bodies:
        print(b.get_points_global())
        print(b.linear_velocity)
        print(b.rotational_velocity)
        print()
    
    # for i in range(190):
    #   inc_index()
    
    while self.running:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          break
      
        if event.type == pygame.KEYDOWN:
          if event.key == pygame.K_RIGHT:
            inc_index()

          elif event.key == pygame.K_LEFT:
            dec_index()
            
          elif event.key == pygame.K_s:
            with open('save', 'wb') as f:
              pickle.dump(self.engine, f)
            print('saved')

        if event.type == pygame.MOUSEBUTTONDOWN:
          self.mouse_down = True
          
        if event.type == pygame.MOUSEBUTTONUP:
          self.mouse_down = False
      self.screen.fill('white')  
          
      # draw the objects here
      for b in self.engine.bodies:
        Polygon(b).draw(self.screen)
        draw_arrow(b.center_of_mass, b.center_of_mass + b.linear_velocity, self.screen)

      if cd:
        for p in cd.contact_points:
          pygame.draw.circle(self.screen, (0, 0, 0), world_to_screen(p), 5)
        
      pygame.display.flip()
      self.clock.tick(60)

    pygame.quit()
    
  
  def play(self):
    self.running = True
    
    while self.running:
      screen_click = False
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          break
        
        if event.type == pygame.MOUSEBUTTONDOWN:
          self.mouse_down = True
          
        if event.type == pygame.MOUSEBUTTONUP:
          self.mouse_down = False
          screen_click = True
          
      if screen_click:
        middle = screen_to_world(Vector2(pygame.mouse.get_pos()))[0]
        d = 50
        points = [
            Vector2(-d,  -d) + middle,
            Vector2(d,  -d) +middle,
            Vector2(d, d) + middle,
            Vector2(-d, d) +middle,
        ]
        self.engine.add_polygonal_body(points)

      self.screen.fill('white')
      # draw the objects here
      for b in self.engine.bodies:
        Polygon(b).draw(self.screen)
        draw_arrow(b.center_of_mass, b.center_of_mass + b.linear_velocity, self.screen)
      
      self.engine.update(1 / 60)
      pygame.display.flip()
      
      
      self.clock.tick(60)
    pygame.quit()

if __name__ == '__main__':
  c = Controller()
  c.play()