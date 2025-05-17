import pickle
from typing import cast
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from collusion import CollusionData, avg, collide
from constants import GRAVITY, SCREEN_HEIGHT, SCREEN_WIDTH
from classes import Polygon
from engine import Engine
from helper import get_square, rot_90_c, screen_to_world, world_to_screen
from copy import deepcopy

from input import MouseEvent
from ui import UILayer, label

# class Polygon:
#   def __init__(self, engine_polygon: Polygon) -> None:
#     """
#       wrapper around engine polygon, including methods to draw
#       points: global (word) coordinates
#     """
#     self.engine_polygon = engine_polygon
#     if self.engine_polygon.mass > 0:
#       # if self.engine_polygon.resting:
#       #   self.fill_color = (0, 255, 0)
#       # else:
#       self.fill_color = (255, 0, 0)
#     else:
#       self.fill_color = (0, 0, 255)

#     self.border_color = tuple([200 if c == 0 else c for c in self.fill_color])

#   def draw(self, surface: Surface):
#     screen_points = world_to_screen(self.engine_polygon.get_points_global())
#     mid = avg(screen_points)
#     thickness = 2
#     pygame.draw.polygon(surface, self.fill_color, screen_points)
#     lab = label(str(self.engine_polygon.body_id), 'Arial', 10)
#     rect = pygame.Rect((0, 0), (lab.get_width(), lab.get_height()))
#     rect.center = (int(mid.x), int(mid.y))
#     surface.blit(lab, rect)

def draw_polygon(polygon: Polygon, surface: Surface):
  if polygon.mass > 0:
    # if self.engine_polygon.resting:
    #   self.fill_color = (0, 255, 0)
    # else:
    fill_color = (255, 0, 0)
  else:
    fill_color = (0, 0, 255)
  border_color = tuple([200 if c == 0 else c for c in fill_color])
  border_thickness = 2
  
  screen_points = world_to_screen(polygon.get_points_global())
  mid = avg(screen_points)
  
  pygame.draw.polygon(surface, fill_color, screen_points)
  lab = label(str(polygon.body_id), 'Arial', 10)
  rect = pygame.Rect((0, 0), (lab.get_width(), lab.get_height()))
  rect.center = (int(mid.x), int(mid.y))
  surface.blit(lab, rect)

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

    for y in [ 200]:
      p1 = self.engine.add_polygonal_body(
        [
          Vector2(0, 0) + Vector2(400, y),
          Vector2(100, 0) + Vector2(400, y),
          Vector2(100, 100) + Vector2(400, y),
          Vector2(0, 100) + Vector2(400, y)
        ]
      )


    
    # for detecting clicks
    self.mouse_down = False
    
    self.mode = 1
  
  def debug_mode(self):
    self.running = True
    
    saves: list[Engine] = [self.engine]
    idx: int = 0 # points to current state
    last_frame_collusions: list[CollusionData] = []
    
    def inc_index():
      nonlocal idx
      nonlocal last_frame_collusions
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
        print(b.body_id)
        print(f'COM: {b.center_of_mass}')
        print(f'rot_dis: {b.rotational_displacement}')
        print(f'linear accel: {b.linear_acceleration}')
        print(f'linear vel: {b.linear_velocity}')
        print(f'rot: vel: {b.rotational_velocity}')
        print(f'resting: {b.resting}')
        print()
      last_frame_collusions = cols
    
    def dec_index():
      nonlocal idx
      nonlocal last_frame_collusions
      idx = max(0, idx - 1)
      print(f'go back to state {idx}')
      self.engine = saves[idx]
      print(f'state: {idx}')
      for b in self.engine.bodies:
        print(b.get_points_global())
        print(b.linear_velocity)
        print(b.rotational_velocity)
        print()


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
            
          elif event.key == pygame.K_p:
            for i in range(100):
              inc_index()

        if event.type == pygame.MOUSEBUTTONDOWN:
          self.mouse_down = True
          
        if event.type == pygame.MOUSEBUTTONUP:
          self.mouse_down = False
      self.screen.fill('white')

      # draw the objects here
      for b in self.engine.bodies:
        draw_polygon(b, self.screen)
        draw_arrow(b.center_of_mass, b.center_of_mass + b.linear_velocity, self.screen)

      for cd in last_frame_collusions:
        for p in cd.contact_points:
          pygame.draw.circle(self.screen, (0, 0, 0), world_to_screen(p), 5)
      
      pygame.display.flip()
      self.clock.tick(60)
    pygame.quit()
  
  def play(self):
    self.running = True
    
    while self.running:
      
      mouse_events: list[MouseEvent] = []
      mouse_pos_frame = Vector2(pygame.mouse.get_pos())
      mouse_events.append(MouseEvent(mouse_pos_frame, 'hover'))

      screen_click = False
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          break
        
        if event.type == pygame.MOUSEBUTTONDOWN:
          mouse_events.append(MouseEvent(mouse_pos_frame, 'mousedown'))
          self.mouse_down = True
        
        if event.type == pygame.MOUSEBUTTONUP:
          mouse_events.append(MouseEvent(mouse_pos_frame, 'mouseup'))
          if self.mouse_down:
            screen_click = True
          self.mouse_down = False
        
        if event.type == pygame.KEYDOWN:
          # clear 
          if event.key == pygame.K_c:
            print('removed all movable entities')
            self.engine.bodies = [b for b in self.engine.bodies if b.mass < 0]
            self.engine.id_gen = len(self.engine.bodies)
            
          elif event.key == pygame.K_1:
            self.mode = 1
          elif event.key == pygame.K_2:
            self.mode = 2
          elif event.key == pygame.K_3:
            pass
      
      if screen_click:
        mouse_events.append(MouseEvent(mouse_pos_frame, 'click'))
        

      
      # say we have a click / hover event
      # - first, make the UI consume the click / hover / mousedown / mouseup
      # - then, if still there, pass on to the engine
      
      # engine preupdate
      # - tell the engine all the events that have occured
      # - so, clicks transformed into world coordinates
      # - also any unconsumed hover, make the color change or something
      self.engine.preupdate([MouseEvent(screen_to_world(e.position), e.type) for e in mouse_events])
      
      self.screen.fill('white')
      # draw engine items
      for b in self.engine.bodies:
        draw_polygon(b, self.screen)
        draw_arrow(b.center_of_mass, b.center_of_mass + b.linear_velocity, self.screen)
      
      
      self.engine.update(1 / 60)
      
      pygame.display.flip()
      self.clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
  # c = Controller()
  # c.play()
  l = UILayer()
  l.play()