
from copy import deepcopy
from dataclasses import dataclass

import pygame

class MyClass:
    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

obj = MyClass(1, 2, 3, 'a')

for attribute_name in obj.__dict__:
    attribute_value = getattr(obj, attribute_name)
    if isinstance(attribute_value, int):
      
      print(f"Attribute: {attribute_name}, Value: {attribute_value}")

