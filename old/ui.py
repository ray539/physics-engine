from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, cast
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from common import Add, CircleInformation, Delete, Drag, PolygonInformation, State, StateManager, circle_graphic, polygon_graphic, square_graphic, triangle_graphic
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from abc import ABC, abstractmethod
from collections.abc import Callable
from engine import Engine
from helper import to_tuple
from input import MouseEvent
from old.ui_library import ButtonWith, Container, Controlled, MySurface, PositionedUINode, UINode, label, globals
pygame.init()



class UILayer:
  """
    controller for the UI
  """
  def __init__(self, gsm: StateManager, engine: Engine) -> None:        
    self.gsm = gsm
    self.gsm.add_subscriber(self)

    def get_options_add_dropdown() -> list[UINode]:
      print('get_options_dropdown')
      if not isinstance(gsm.current_state, Add):
        return []
      
      ans: list[UINode] = []
      print('get_options_add')
      
      def get_new_add_state(selected_id: str):
        new_add_state = deepcopy(gsm.current_state)
        new_add_state.selected_id = selected_id  # type: ignore
        return new_add_state

      for o in gsm.current_state.avaliable_objects:
        this_id = o.id
        
        def is_outline(this_id:str = this_id) -> bool:
          return gsm.current_state.selected_id == this_id # type: ignore
        
        def handle_click(e: MouseEvent, n: UINode, this_id:str=this_id):
          gsm.set_state(get_new_add_state(this_id))

        if isinstance(o, CircleInformation):
          ans.append(
            MySurface(
              surface = circle_graphic(50),
              show_outline = is_outline,
              on_click= handle_click
            )
          )
        elif isinstance(o, PolygonInformation):
          ans.append(
            MySurface(
              surface = polygon_graphic(o.local_points, 50), 
              show_outline = is_outline,
              on_click=handle_click
            )
          )
          
      return ans
    
    options = Container(
      direction='col',
      child_spacing=0,
      padding=0,
      children=[
        Container(
          child_alignment='space_between',
          min_width=300,
          padding=2,
          children=[
            MySurface(
              label('select mode', 'Arial', 15)
            )
          ]
        ),
        Container(
          children=[
            ButtonWith(
              text='add',
              font_size=20,
              gap=10,
              background_color=lambda: (255, 200, 200, 255) if isinstance(gsm.current_state, Add) else (200, 200, 200, 255),
              on_click=lambda e, n: gsm.set_state(gsm.ADD_STATE),
              dropdown_content=Container(
                background_color=(230, 230, 230, 255),
                child_alignment='left',
                children=[
                  Container(
                    padding=10,
                    background_color=(200, 200, 200, 255),
                    children= lambda: get_options_add_dropdown()
                  ),
                  ButtonWith(
                    text='more..',
                    dropdown_content=None,
                    font_size=20
                  )
                ],
                padding=10,
                child_spacing=10
              ),
            ),
            ButtonWith(
              text='drag',
              font_size=20,
              background_color=lambda: (255, 200, 200, 255) if isinstance(gsm.current_state, Drag) else (200, 200, 200, 255),
              on_click=lambda e,n: gsm.set_state(Drag()),
              dropdown_content=None
            ),
            ButtonWith(
              text='delete',
              font_size=20,
              background_color=lambda: (255, 200, 200, 255) if isinstance(gsm.current_state, Delete) else (200, 200, 200, 255),
              on_click=lambda e,n: gsm.set_state(Delete()),
              dropdown_content=None
            ),
            ButtonWith(
              text='clear..', 
              font_size=20, 
              gap=10,
              dropdown_content=Container(
                direction='col',
                children=[
                  ButtonWith(text='movable items', font_size=20, dropdown_content=None, on_click=lambda e, n: engine.remove_movable_bodies()),
                  ButtonWith(text='all items', font_size=20, dropdown_content=None),
                ],
                background_color=(230, 230, 230, 255),
                min_height=300,
                padding=5
              )
            )
          ],
          child_alignment='right',
          background_color=(230, 230, 230, 255),
          padding=5,
          min_width=300
        )
      ]
    )
    options = PositionedUINode(
      options,
      lambda n: Vector2(SCREEN_WIDTH - n.width_height[0] - 20, 20)
    )
    load_save = Container(
      child_alignment='left',
      background_color=(230, 230, 230, 255),
      padding=5,
      min_width=300,
      children=[
        ButtonWith(
          text='load',
          dropdown_content=None,
        ),
        ButtonWith(
          text='save',
          dropdown_content=None
        ),
      ]
    )
    load_save = PositionedUINode(load_save, Vector2(20, 20))
    self.positioned_nodes = [options, load_save]

  def handle_input(self, mouse_event: MouseEvent):
    """
      consume the mouse_event. \n
      return the mouse_event if unconsumed, else none
    """
    if 'mouseup' in mouse_event.types:
      pass
    
    globals.state_changed_in_frame = self.gsm.has_notification(self)
    if globals.state_changed_in_frame:
      print('ui_layer received')
    
    globals.calculated_in_frame.clear()
    self.gsm.consume_notification(self)
    
    # update (the thing to be rendered, including fetching the new state and stuff)
    for n in self.positioned_nodes:
      n.draw_node(Surface((0, 0)))
    
    best = None
    for p_node in self.positioned_nodes:
      best = p_node.node.get_best_hitbox(mouse_event)
      if best:
        break
    self.best = best
    all_hitboxes = [h for p_node in self.positioned_nodes for h in p_node.node.get_all_hitboxes()]
    for h in all_hitboxes:
      h.update_mouse_over(mouse_event, h == best)
    
    return mouse_event if (best == None) else None
  
  def draw(self, surface: Surface):
    for p_node in self.positioned_nodes:
      p_node.draw_node(surface)
    if self.best:
      pygame.draw.rect(surface, (0, 0, 255), self.best.rect, 2)


  # 1057 119 50 50 -> triangle hitbox
  # 1221 56 44 33 -> add button hitbox
  def test(self):
    
    a = Surface((0, 0))
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), set([])))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), set(['mousedown'])))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), set()))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), set(['mouseup'])))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), set()))
    self.draw(a)
    
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), set()))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), set(['mousedown'])))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), set()))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), set(['mouseup'])))
    self.draw(a)
    
    print(self.gsm.current_state)
    
    
  
  # for debugging, draw only UI layer
  def play(self):
    
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = True
    self.mouse_down = False
    while self.running:      
      mouse_pos_frame = Vector2(pygame.mouse.get_pos())
      mouse_event: MouseEvent = MouseEvent(mouse_pos_frame, set())
      
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          
        if event.type == pygame.MOUSEBUTTONDOWN:
          mouse_event.types.add('mousedown')
          self.mouse_down = True
        
        if event.type == pygame.MOUSEBUTTONUP:
          mouse_event.types.add('mouseup')
          self.mouse_down = False

      # process mouse events
      self.handle_input(mouse_event)
      
      # draw nodes
      self.screen.fill((255, 255, 255))
      for x in range(0, SCREEN_WIDTH, 50):
        pygame.draw.line(self.screen, (200, 200, 200), Vector2(x, 0), Vector2(x, SCREEN_HEIGHT))
        
      self.draw(self.screen)
      pygame.display.flip()
      self.clock.tick(60)