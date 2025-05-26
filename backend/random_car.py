import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Movement Modes")

# Load and scale background
background = pygame.image.load("background.jpg")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)

# Fonts
font = pygame.font.SysFont(None, 36)

# Buttons
manual_button = pygame.Rect(600, 20, 150, 40)
auto_button = pygame.Rect(600, 70, 150, 40)

# Clock
clock = pygame.time.Clock()

# Load car image (replace with your actual image)
car_image = pygame.image.load("car.png")  # should be top-down
car_image = pygame.transform.scale(car_image, (60, 30))  # size should match the model

# Car object using the bicycle model
class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0  # radians
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.2
        self.steering_angle = 0  # radians
        self.max_steering = math.radians(30)  # max 30 degree steering
        self.length = 50  # distance between front and rear axles

    def draw(self, surface):
        rotated_car = pygame.transform.rotate(car_image, -math.degrees(self.angle))
        rect = rotated_car.get_rect(center=(self.x, self.y))
        surface.blit(rotated_car, rect.topleft)

    def move_manual(self, keys):
        # Accelerate
        if keys[pygame.K_UP]:
            self.speed = min(self.speed + self.acceleration, self.max_speed)
        elif keys[pygame.K_DOWN]:
            self.speed = max(self.speed - self.acceleration, -self.max_speed / 2)
        else:
            self.speed *= 0.95  # Friction

        # Steering (only affects when moving)
        if keys[pygame.K_LEFT]:
            self.steering_angle = max(self.steering_angle - math.radians(2), -self.max_steering)
        elif keys[pygame.K_RIGHT]:
            self.steering_angle = min(self.steering_angle + math.radians(2), self.max_steering)
        else:
            self.steering_angle *= 0.8  # return wheels toward center

        self.update_position()

    def move_auto(self):
        self.speed = self.max_speed * 0.6
        self.steering_angle = random.uniform(-self.max_steering, self.max_steering)
        self.update_position()

    def update_position(self):
        if self.steering_angle:
            turning_radius = self.length / math.tan(self.steering_angle)
            angular_velocity = self.speed / turning_radius
        else:
            angular_velocity = 0

        self.angle += angular_velocity
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

        # Clamp to screen
        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))

# Initialize car and mode
car = Car(400, 300)
mode = 'manual'

# Game loop
running = True
while running:
    screen.blit(background, (0, 0))

    # Draw buttons
    pygame.draw.rect(screen, GREEN if mode == 'manual' else WHITE, manual_button)
    pygame.draw.rect(screen, GREEN if mode == 'auto' else WHITE, auto_button)
    screen.blit(font.render("Manual Mode", True, BLACK), (manual_button.x + 10, manual_button.y + 5))
    screen.blit(font.render("Auto Mode", True, BLACK), (auto_button.x + 20, auto_button.y + 5))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if manual_button.collidepoint(event.pos):
                mode = 'manual'
            elif auto_button.collidepoint(event.pos):
                mode = 'auto'

    keys = pygame.key.get_pressed()
    if mode == 'manual':
        car.move_manual(keys)
    else:
        car.move_auto()

    car.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
