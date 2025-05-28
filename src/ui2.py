from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, cast
import pygame
from pygame.math import Vector2
from pygame.surface import Surface
from common import Add, CircleInformation, Delete, Drag, PolygonInformation, State, StateManager, circle_graphic, label, polygon_graphic, square_graphic, triangle_graphic
from constants import SCREEN_HEIGHT, SCREEN_WIDTH
from abc import ABC, abstractmethod
from collections.abc import Callable
from engine import Engine
from helper import to_tuple
from ui_lib2 import ButtonWith, Container, Expr, MySurface, PositionedUINode, UIEngine, UINode, MouseEvent
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
        
        def handle_click(e: MouseEvent, this_id: str = this_id):
          gsm.set_state(get_new_add_state(this_id))

        if isinstance(o, CircleInformation):
          ans.append(
            MySurface(
              id=f'{o.id} (graphic)',
              surface = circle_graphic(50),
              show_outline = Expr(is_outline),
              on_click = handle_click
            )
          )
        elif isinstance(o, PolygonInformation):
          ans.append(
            MySurface(
              id=f'{o.id} (graphic)',
              surface = polygon_graphic(o.local_points, 50), 
              show_outline = Expr(is_outline),
              on_click=handle_click
            )
          )
          
      return ans

    options = Container(
      id='options-1',
      direction='col',
      child_spacing=0,
      padding=0,
      children=Expr(lambda: [
        Container(
          id='options-2',
          child_alignment='space_between',
          min_width=300,
          padding=2,
          children=[
            MySurface(
              id='select mode',
              surface = label('select mode', 'Arial', 15)
            )
          ]
        ),
        Container(
          id='options-3',
          children=[
            ButtonWith(
              id='add',
              text='add',
              font_size=20,
              gap=10,
              background_color=Expr(lambda: (255, 200, 200, 255) if isinstance(gsm.current_state, Add) else (200, 200, 200, 255)),
              on_click=lambda e, n: (
                gsm.set_state(gsm.ADD_STATE)
              ),
              show_dropdown=Expr(lambda: isinstance(gsm.current_state, Add)),
              dropdown_content=Container(
                id='add-dropdown',
                background_color=(230, 230, 230, 255),
                child_alignment='left',
                children=[
                  Container(
                    id='shapes-cont',
                    padding=10,
                    background_color=(200, 200, 200, 255),
                    children= Expr(get_options_add_dropdown)
                  ),
                  ButtonWith(
                    id='more..',
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
              id='drag',
              text='drag',
              font_size=20,
              background_color=Expr(lambda: (255, 200, 200, 255) if isinstance(gsm.current_state, Drag) else (200, 200, 200, 255)),
              on_click=lambda e ,n: gsm.set_state(Drag()),
              dropdown_content=None
            ),
            ButtonWith(
              id='delete',
              text='delete',
              font_size=20,
              background_color=Expr(lambda: (255, 200, 200, 255) if isinstance(gsm.current_state, Delete) else (200, 200, 200, 255)),
              on_click=lambda e,n: gsm.set_state(Delete()),
              dropdown_content=None
            ),
            ButtonWith(
              id='clear',
              text='clear..', 
              font_size=20, 
              gap=10,
              dropdown_content=Container(
                direction='col',
                children=[
                  ButtonWith(id='movable', text='movable items', font_size=20, dropdown_content=None, on_click=lambda e, n: engine.remove_movable_bodies()),
                  ButtonWith(id='all items', text='all items', font_size=20, dropdown_content=None),
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
      ])
    )
    options = PositionedUINode(
      options,
      lambda n: Vector2(SCREEN_WIDTH - n.get_width_height()[0] - 20, 20)
    )
    
    load_save = Container(
      child_alignment='left',
      background_color=(230, 230, 230, 255),
      padding=5,
      min_width=300,
      children=Expr(lambda: [
        ButtonWith(
          text='load',
          dropdown_content=None,
        ),
        ButtonWith(
          text='save',
          dropdown_content=None
        ),
      ])
    )
    
    load_save = PositionedUINode(load_save, Vector2(20, 20))
    
    # def f1():
    #   print('here1')
    #   return isinstance(gsm.current_state, Add)
    
    # def f2():
    #   print('here2')
    #   return isinstance(gsm.current_state, Drag)
    
    # test = Container(
    #   children=Expr(lambda:[
    #     MySurface(
    #       surface=Surface((50, 50)),
    #       show_outline=Expr(f1),
    #       on_click=lambda e: ( gsm.set_state(Add([], '')))
    #     ),
    #     MySurface(
    #       surface=Surface((50, 50)),
    #       show_outline=Expr(f2),
    #       on_click=lambda e: ( gsm.set_state(Drag()))
    #     ),
    #   ])
    # )
    # test = PositionedUINode(test, Vector2(20, 20))
    
    self.ui_engine = UIEngine(gsm)
    self.ui_engine.positioned_nodes = [options, load_save]
  

  def handle_input(self, mouse_event: MouseEvent):
    return self.ui_engine.handle_input(mouse_event)
    
  def draw(self, surface: Surface):
    self.ui_engine.draw(surface)

  # 1057 119 50 50 -> triangle hitbox
  # 1221 56 44 33 -> add button hitbox
  def test(self):
    
    a = Surface((0, 0))
    
    # click add
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'mousedown'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'mouseup'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'none'))
    self.draw(a)
    
    # click triangle
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), 'mousedown'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1057, 119) + Vector2(25, 25), 'mouseup'))
    self.draw(a)
    
    # click add
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'mousedown'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'mouseup'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(1221, 56) + Vector2(10, 19), 'none'))
    self.draw(a)
    
    print(self.gsm.current_state)
    
    print('here')

  
  def test2(self):
    a = Surface((0, 0))
    self.handle_input(MouseEvent(Vector2(45, 57), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(45, 57) + Vector2(10, 19), 'mousedown'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(45, 57) + Vector2(10, 19), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(45, 57) + Vector2(10, 19), 'mouseup'))
    self.draw(a)
    
    
    self.handle_input(MouseEvent(Vector2(127, 37), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(127, 37), 'mousedown'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(127, 37), 'none'))
    self.draw(a)
    self.handle_input(MouseEvent(Vector2(127, 37), 'mouseup'))
    self.draw(a)
    
    pass
  
  # for debugging, draw only UI layer
  def play(self):
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    self.clock = pygame.time.Clock()
    self.running = True
    self.mouse_down = False
    while self.running:      
      mouse_pos_frame = Vector2(pygame.mouse.get_pos())
      mouse_event: MouseEvent = MouseEvent(mouse_pos_frame, 'none')
      
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
          
        if event.type == pygame.MOUSEBUTTONDOWN:
          mouse_event.type = 'mousedown'
          self.mouse_down = True
        
        if event.type == pygame.MOUSEBUTTONUP:
          mouse_event.type = 'mouseup'
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