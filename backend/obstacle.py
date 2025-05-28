import pygame
import sys
import math
import random

# Load car sprite
car_image = pygame.image.load("car.png")
car_image = pygame.transform.scale(car_image, (60, 30))

# ================================
# Obstacle Class
# ================================

class Obstacle:
    def draw(self, surface):
        pass
    def is_clicked(self, pos):
        return False
    def move_to(self, x, y):
        pass
    def rotate(self, amount):
        pass

class CarObstacle(Obstacle):
    def __init__(self, x, y):
        self.image = pygame.transform.scale(car_image, (60, 30))
        self.angle = 0
        self.x = x
        self.y = y

    def draw(self, surface):
        rotated = pygame.transform.rotate(self.image, -self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect.topleft)

    def is_clicked(self, pos):
        rect = self.image.get_rect(center=(self.x, self.y))
        return rect.collidepoint(pos)

    def move_to(self, x, y):
        self.x, self.y = x, y

    def rotate(self, amount):
        self.angle = (self.angle + amount) % 360

    def draw_outline(self, surface):
        if hasattr(self, 'x') and hasattr(self, 'y'):
            pygame.draw.circle(surface, (255, 0, 0), (int(self.x), int(self.y)), 40, 2)

class CartObstacle(Obstacle):
    def __init__(self, x, y):
        self.image = pygame.Surface((40, 20), pygame.SRCALPHA)
        self.image.fill((0, 100, 200))
        self.angle = 0
        self.x = x
        self.y = y

    def draw(self, surface):
        rotated = pygame.transform.rotate(self.image, -self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect.topleft)

    def is_clicked(self, pos):
        rect = self.image.get_rect(center=(self.x, self.y))
        return rect.collidepoint(pos)

    def move_to(self, x, y):
        self.x, self.y = x, y

    def rotate(self, amount):
        self.angle = (self.angle + amount) % 360

    def draw_outline(self, surface):
        if hasattr(self, 'x') and hasattr(self, 'y'):
            pygame.draw.circle(surface, (255, 0, 0), (int(self.x), int(self.y)), 40, 2)

class CircleObstacle(Obstacle):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15

    def draw(self, surface):
        pygame.draw.circle(surface, (0, 200, 100), (self.x, self.y), self.radius)

    def is_clicked(self, pos):
        return math.hypot(pos[0] - self.x, pos[1] - self.y) <= self.radius

    def move_to(self, x, y):
        self.x, self.y = x, y

    def draw_outline(self, surface):
        if hasattr(self, 'x') and hasattr(self, 'y'):
            pygame.draw.circle(surface, (255, 0, 0), (int(self.x), int(self.y)), 40, 2)

class LineSegment(Obstacle):
    def __init__(self, start_pos, end_pos):
        self.start = start_pos
        self.end = end_pos
        self.color = (255, 255, 0)
        self.thickness = 7

    def draw(self, surface):
        pygame.draw.line(surface, self.color, self.start, self.end, self.thickness)

    def is_clicked(self, pos):
        # Optional: implement pixel-perfect check or bounding box
        return False

def segments_intersect(p1, p2, q1, q2):
    def ccw(a, b, c):
        return (c[1]-a[1]) * (b[0]-a[0]) > (b[1]-a[1]) * (c[0]-a[0])
    return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))
