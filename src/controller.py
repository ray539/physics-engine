from abc import ABC
import pickle
from typing import Literal, cast
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from collusion import CollusionData, avg, collide
from common import StateManager
from constants import GRAVITY, SCREEN_HEIGHT, SCREEN_WIDTH
from classes import Polygon
from engine import Engine
from helper import get_square, rot_90_c, screen_to_world, world_to_screen
from copy import deepcopy
from ui_lib2 import MouseEvent
from ui2 import UILayer


# each object has a 'click' event handler
# this is how we will interact with the objects 
class Controller:
  def __init__(self) -> None:
    pygame.init()
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = False
    
    self.global_state = StateManager()
    self.engine = Engine(self.global_state)
    
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
    self.ui_layer = UILayer(self.global_state, self.engine)
  
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
      self.engine.draw(self.screen)
      
      for cd in last_frame_collusions:
        for p in cd.contact_points:
          pygame.draw.circle(self.screen, (0, 0, 0), world_to_screen(p), 5)
      
      pygame.display.flip()
      self.clock.tick(60)
    pygame.quit()
  
  def play(self):
    
    self.running = True
    while self.running:
      mouse_pos_frame = Vector2(pygame.mouse.get_pos())
      mouse_event: MouseEvent = MouseEvent(mouse_pos_frame, 'none')

      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          break
        
        if event.type == pygame.MOUSEBUTTONDOWN:
          mouse_event.type = 'mousedown'
        
        if event.type == pygame.MOUSEBUTTONUP:
          mouse_event.type = 'mouseup'
        
        if event.type == pygame.KEYDOWN:
          # clear 
          if event.key == pygame.K_c:
            print('removed all movable entities')
            self.engine.bodies = [b for b in self.engine.bodies if b.mass < 0]
            self.engine.id_gen = len(self.engine.bodies)
      
      # say we have a click / hover event
      # - first, make the UI consume the click / hover / mousedown / mouseup
      # - then, if still there, pass on to the engine
      
      mouse_event_2 = self.ui_layer.handle_input(mouse_event)
      self.engine.handle_input(mouse_event_2)
      
      # draw items
      self.screen.fill('white')

      self.engine.draw(self.screen)
      self.ui_layer.draw(self.screen)
            
      self.engine.update(1 / 60)
      pygame.display.flip()
      self.clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
  gsm = StateManager()
  e = Engine(gsm)
  l = Controller()
  l.play()