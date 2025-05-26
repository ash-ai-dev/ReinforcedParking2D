import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600  # Wider screen
GAME_WIDTH = 600           # Game area
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Movement Modes")

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

# Obstacles
obstacles = []

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
# Car Class
# ================================
class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.2
        self.steering_angle = 0
        self.max_steering = math.radians(30)
        self.length = 50

    def draw(self, surface):
        rotated_car = pygame.transform.rotate(car_image, -math.degrees(self.angle))
        rect = rotated_car.get_rect(center=(self.x, self.y))
        surface.blit(rotated_car, rect.topleft)

    def move_manual(self, keys):
        if keys[pygame.K_UP]:
            self.speed = min(self.speed + self.acceleration, self.max_speed)
        elif keys[pygame.K_DOWN]:
            self.speed = max(self.speed - self.acceleration, -self.max_speed / 2)
        else:
            self.speed *= 0.95

        if keys[pygame.K_LEFT]:
            self.steering_angle = max(self.steering_angle - math.radians(2), -self.max_steering)
        elif keys[pygame.K_RIGHT]:
            self.steering_angle = min(self.steering_angle + math.radians(2), self.max_steering)
        else:
            self.steering_angle *= 0.8

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

        # Clamp to screen bounds
        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))


# ================================
# Functions
# ================================
def draw_ui(mode):
    screen.blit(background, (0, 0))
    pygame.draw.rect(screen, GREEN if mode == 'manual' else WHITE, manual_button)
    pygame.draw.rect(screen, GREEN if mode == 'auto' else WHITE, auto_button)
    screen.blit(font.render("Manual Mode", True, BLACK), (manual_button.x + 10, manual_button.y + 5))
    screen.blit(font.render("Auto Mode", True, BLACK), (auto_button.x + 20, auto_button.y + 5))


def handle_events():
    global mode, running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if manual_button.collidepoint(event.pos):
                mode = 'manual'
            elif auto_button.collidepoint(event.pos):
                mode = 'auto'


def update_logic(car, mode):
    keys = pygame.key.get_pressed()
    if mode == 'manual':
        car.move_manual(keys)
        print("Hello")
    elif mode == 'auto':
        print("Bye")
        car.move_auto()


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


# ================================
# Car Class
# ================================
class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.2
        self.steering_angle = 0
        self.max_steering = math.radians(30)
        self.length = 50

    def draw(self, surface):
        rotated_car = pygame.transform.rotate(car_image, -math.degrees(self.angle))
        rect = rotated_car.get_rect(center=(self.x, self.y))
        surface.blit(rotated_car, rect.topleft)

    def move_manual(self, keys):
        if keys[pygame.K_UP]:
            self.speed = min(self.speed + self.acceleration, self.max_speed)
        elif keys[pygame.K_DOWN]:
            self.speed = max(self.speed - self.acceleration, -self.max_speed / 2)
        else:
            self.speed *= 0.95

        if keys[pygame.K_LEFT]:
            self.steering_angle = max(self.steering_angle - math.radians(2), -self.max_steering)
        elif keys[pygame.K_RIGHT]:
            self.steering_angle = min(self.steering_angle + math.radians(2), self.max_steering)
        else:
            self.steering_angle *= 0.8

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

        # Clamp to screen bounds
        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))


# ================================
# Functions
# ================================


def update_logic(car, mode):
    keys = pygame.key.get_pressed()
    if mode == 'manual':
        car.move_manual(keys)
    else:
        car.move_auto()

def draw_ui(mode):
    screen.blit(background, (0, 0))
    
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
        print(mode)
        draw_ui(mode)
        car.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
