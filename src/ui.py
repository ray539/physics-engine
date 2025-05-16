import pygame

def label(text: str, font_name: str, font_size: int, highlight: bool = False):
  font = pygame.font.SysFont(font_name, font_size)
  a1 = font.render(text, True, (0, 0, 0))
  b1 = pygame.Surface((a1.get_width() + 10, a1.get_height() + 10))
  b1.fill((0, 200, 0) if highlight else (200, 200, 200))
  b1.blit(a1, (5, 5))
  return b1