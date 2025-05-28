import pygame
import sys
import math
import random

from car import Car
from obstacle import *

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600  # Wider screen
GAME_WIDTH = 600           # Game area
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Movement Modes")

# Obstacles
obstacles = []
dynamic_yellow_obstacles = []



def extract_yellow_lines_near_car(surface, car_position, sensor_range):
    yellow_threshold = 60
    width, height = surface.get_size()
    pixels = pygame.surfarray.pixels3d(surface)
    cx, cy = car_position

    new_positions = set()

    for x in range(max(0, cx - sensor_range), min(width, cx + sensor_range), 3):
        for y in range(max(0, cy - sensor_range), min(height, cy + sensor_range), 3):
            if math.hypot(x - cx, y - cy) > sensor_range:
                continue
            r, g, b = pixels[x][y]
            if abs(r - 255) < yellow_threshold and abs(g - 255) < yellow_threshold and b < yellow_threshold:
                new_positions.add((x, y))

    return new_positions



# Load and scale background
background = pygame.image.load("background.jpg")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Colors and fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
font = pygame.font.SysFont(None, 36)

# Buttons
manual_button = pygame.Rect(600, 20, 150, 40)
auto_button = pygame.Rect(600, 70, 150, 40)

# Load car sprite
car_image = pygame.image.load("car.png")
car_image = pygame.transform.scale(car_image, (60, 30))

# UI Obstacle Selector Buttons
selector_buttons = {
    "car": pygame.Rect(20, 540, 80, 40),
    "cart": pygame.Rect(120, 540, 80, 40),
    "circle": pygame.Rect(220, 540, 80, 40)
}

selected_type = "car"
dragging_obstacle = None
offset_x, offset_y = 0, 0

# Clock
clock = pygame.time.Clock()


# ================================
# Functions
# ================================

def update_dynamic_yellow_obstacles(car_pos, sensor_range):
    global dynamic_yellow_obstacles
    new_positions = extract_yellow_lines_near_car(background, car_pos, sensor_range)

    # Current positions of dynamic obstacles
    current_positions = set((obs.x, obs.y) for obs in dynamic_yellow_obstacles)

    # Remove obstacles no longer in range
    dynamic_yellow_obstacles = [obs for obs in dynamic_yellow_obstacles if (obs.x, obs.y) in new_positions]

    # Add new obstacles found (avoid duplicates)
    added_positions = set((obs.x, obs.y) for obs in dynamic_yellow_obstacles)
    for pos in new_positions:
        if pos not in added_positions:
            dynamic_yellow_obstacles.append(LineSegment(pos[0], pos[1]))


def update_logic(car, mode):
    keys = pygame.key.get_pressed()
    if mode == 'manual':
        car.move_manual(keys)
    elif mode == 'auto':
        car.cast_sensor(obstacles, screen)
        car.move_auto(screen)


def draw_ui(mode):
    screen.blit(background, (0, 0))

    for obs in dynamic_yellow_obstacles:
        obs.draw(screen)
    
    # Choose colors based on current mode
    manual_color = (100, 255, 100) if mode == 'manual' else (200, 200, 200)
    auto_color = (100, 255, 100) if mode == 'auto' else (200, 200, 200)

    # Draw Manual button
    pygame.draw.rect(screen, manual_color, manual_button)
    manual_text = font.render("Manual", True, BLACK)
    screen.blit(manual_text, (manual_button.x + 10, manual_button.y + 10))

    # Draw Auto button
    pygame.draw.rect(screen, auto_color, auto_button)
    auto_text = font.render("Auto", True, BLACK)
    screen.blit(auto_text, (auto_button.x + 10, auto_button.y + 10))

    # Obstacle selector UI
    for key, rect in selector_buttons.items():
        pygame.draw.rect(screen, (200, 200, 200) if key != selected_type else (0, 200, 0), rect)
        screen.blit(font.render(key.capitalize(), True, BLACK), (rect.x + 5, rect.y + 5))

    # Draw all obstacles
    for obs in obstacles:
        obs.draw(screen)
        if obs == dragging_obstacle:
            obs.draw_outline(screen)

def handle_events():
    global mode, running, selected_type, dragging_obstacle, offset_x, offset_y
    instructions = font.render("Q/E: Rotate   DEL/BACKSPACE: Delete", True, BLACK)
    screen.blit(instructions, (20, 500))   
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False    

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()

            # Check if mode buttons were clicked
            if manual_button.collidepoint((mx, my)):
                print("Mode set to manual")
                mode = 'manual'
                return
            elif auto_button.collidepoint((mx, my)):
                mode = 'auto'
                print("Mode set to auto")
                return

            # Obstacle selector
            for key, rect in selector_buttons.items():
                if rect.collidepoint((mx, my)):
                    selected_type = None if selected_type == key else key
                    return

            # Try to drag existing obstacle
            for obs in reversed(obstacles):  # Top-down
                if obs.is_clicked((mx, my)):
                    dragging_obstacle = obs
                    if hasattr(obs, 'x'):
                        offset_x = mx - obs.x
                        offset_y = my - obs.y
                    return

            # Else, place new obstacle
            if selected_type == "car":
                obstacles.append(CarObstacle(mx, my))
            elif selected_type == "cart":
                obstacles.append(CartObstacle(mx, my))
            elif selected_type == "circle":
                obstacles.append(CircleObstacle(mx, my))


        elif event.type == pygame.MOUSEBUTTONUP:
            dragging_obstacle = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging_obstacle:
                mx, my = pygame.mouse.get_pos()
                dragging_obstacle.move_to(mx - offset_x, my - offset_y)

        elif event.type == pygame.KEYDOWN and dragging_obstacle:
            if event.key == pygame.K_q:
                dragging_obstacle.rotate(-10)
            elif event.key == pygame.K_e:
                dragging_obstacle.rotate(10)
            elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                if dragging_obstacle in obstacles:
                    obstacles.remove(dragging_obstacle)
                    dragging_obstacle = None

# ================================
# Main
# ================================

def main():
    global mode, running
    car = Car(400, 300)
    mode = 'manual'
    running = True

    while running:
        draw_ui(mode)
        handle_events()
        update_logic(car, mode)
        draw_ui(mode)
        car.draw(screen)
        sensor_range = 100
        update_dynamic_yellow_obstacles((int(car.x), int(car.y)), sensor_range)
        car.cast_sensor(obstacles + dynamic_yellow_obstacles, screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
