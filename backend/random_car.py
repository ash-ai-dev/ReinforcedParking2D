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
        self.auto_state = "scanning"   # Initial auto mode state
        self.sensor_data = {}          # Store sensor distances
        self.parked_timer = 0          # Time counter to stop at final state

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

        
    def cast_sensor(self, obstacles, surface):
        sensor_configs = [
            ("Front Left", self.angle - math.pi / 6, (0, 255, 0)),
            ("Front Center", self.angle, (0, 255, 0)),
            ("Front Right", self.angle + math.pi / 6, (0, 255, 0)),
            ("Rear Left", self.angle + math.pi - math.pi / 6, (0, 200, 255)),
            ("Rear Center", self.angle + math.pi, (0, 200, 255)),
            ("Rear Right", self.angle + math.pi + math.pi / 6, (0, 200, 255))
        ]

        max_distance = 150
        font_small = pygame.font.SysFont(None, 20)

        for label, angle, base_color in sensor_configs:
            for dist in range(0, max_distance, 5):
                sx = int(self.x + dist * math.cos(angle))
                sy = int(self.y + dist * math.sin(angle))

                if sx < 0 or sx >= WIDTH or sy < 0 or sy >= HEIGHT:
                    break

                hit = False
                for obj in obstacles:
                    if isinstance(obj, CircleObstacle):
                        if math.hypot(obj.x - sx, obj.y - sy) <= obj.radius:
                            hit = True
                            break
                    elif isinstance(obj, (CarObstacle, CartObstacle)):
                        obj_rect = pygame.Rect(obj.x - 30, obj.y - 15, 60, 30)
                        if obj_rect.collidepoint(sx, sy):
                            hit = True
                            break
                
                if hit:
                    self.sensor_data[label] = dist
                    if dist < 50:
                        color = (255, 0, 0)
                    elif dist < 100:
                        color = (255, 255, 0)
                    else:
                        color = base_color

                    pygame.draw.line(surface, color, (self.x, self.y), (sx, sy), 2)

                    # Draw distance label
                    label_text = font_small.render(f"{label}: {dist}", True, color)
                    surface.blit(label_text, (sx + 5, sy))
                    break
            else:
                # Draw full range if no hit
                end_x = int(self.x + max_distance * math.cos(angle))
                end_y = int(self.y + max_distance * math.sin(angle))
                pygame.draw.line(surface, base_color, (self.x, self.y), (end_x, end_y), 1)


    def move_auto(self, surface):
        self.cast_sensor(obstacles=[], surface=surface)  # Required before using sensor_data

        if self.auto_state == "scanning":
            # Step 1: Check for visual lines
            if self.is_crossing_yellow_line(surface):
                print("Blocked by yellow line — not allowed to cross.")
                self.speed = 0
                return  # Stop movement this frame
            if self.scan_for_parking_lines(surface):
                self.auto_state = "parking"
                print("Yellow lines detected: parking spot found")
                self.speed = 0
                return

            # Existing scanning logic
            self.speed = 2
            front = self.sensor_data.get("Front Center", 200)
            left = self.sensor_data.get("Front Left", 200)
            right = self.sensor_data.get("Front Right", 200)

            if front < 50:
                self.speed = 0
                self.steering_angle = math.radians(-25 if left > right else 25)
            elif left < 50:
                self.steering_angle = math.radians(20)
            elif right < 50:
                self.steering_angle = math.radians(-20)
            else:
                self.steering_angle *= 0.8

        elif self.auto_state == "parking":
            self.execute_parking_maneuver()

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

    def scan_for_parking_lines(self, surface):
        """
        Scans a small region ahead of the car for yellow lines that mark a parking spot.
        """
        scan_distance = 60
        scan_width = 40
        yellow_count = 0

        for offset in range(-scan_width // 2, scan_width // 2, 5):
            sx = int(self.x + scan_distance * math.cos(self.angle) + offset * math.cos(self.angle + math.pi / 2))
            sy = int(self.y + scan_distance * math.sin(self.angle) + offset * math.sin(self.angle + math.pi / 2))

            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                r, g, b = surface.get_at((sx, sy))[:3]
                if r > 200 and g > 200 and b < 100:
                    yellow_count += 1

        return yellow_count >= 5


    def check_parking_space(self, surface):
        # Sample points around the car's position
        sample_offsets = [(-20, -20), (-20, 0), (-20, 20),
                        (0, -20), (0, 0), (0, 20),
                        (20, -20), (20, 0), (20, 20)]

        yellow_pixel_count = 0

        for dx, dy in sample_offsets:
            sx = int(self.x + dx)
            sy = int(self.y + dy)

            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                color = surface.get_at((sx, sy))  # Returns (r, g, b, a)
                r, g, b = color[:3]

                if r > 200 and g > 200 and b < 100:
                    yellow_pixel_count += 1

        # Consider "in a parking space" if a lot of yellow is detected
        self.in_space = yellow_pixel_count >= 4

    def detect_parking_spot(self):
        rear_left = self.sensor_data.get("Rear Left", 200)
        rear_center = self.sensor_data.get("Rear Center", 200)
        rear_right = self.sensor_data.get("Rear Right", 200)

        front_left = self.sensor_data.get("Front Left", 0)
        front_center = self.sensor_data.get("Front Center", 0)
        front_right = self.sensor_data.get("Front Right", 0)

        # Detect U-shape behind and clear space ahead
        rear_closed = rear_left < 80 and rear_center < 80 and rear_right < 80
        front_open = front_left > 120 and front_center > 120 and front_right > 120

        if rear_closed and front_open:
            return True
        return False

    def execute_parking_maneuver(self):
        self.speed = -1  # Start reversing
        self.steering_angle = 0

        self.parked_timer += 1
        if self.parked_timer > 30:
            self.speed = 0
            self.auto_state = "parked"
            print("Car parked.")

    def is_crossing_yellow_line(self, surface):
        """
        Check if the front of the car is crossing a yellow line.
        """
        yellow_threshold = 5
        yellow_count = 0
        check_distance = 25
        check_width = 30

        for offset in range(-check_width // 2, check_width // 2, 5):
            sx = int(self.x + check_distance * math.cos(self.angle) + offset * math.cos(self.angle + math.pi / 2))
            sy = int(self.y + check_distance * math.sin(self.angle) + offset * math.sin(self.angle + math.pi / 2))

            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                r, g, b = surface.get_at((sx, sy))[:3]
                if r > 200 and g > 200 and b < 100:
                    yellow_count += 1

        return yellow_count >= yellow_threshold

# ================================
# Line Class
# ================================

class LineMarker:
    def __init__(self, start_pos, end_pos, color, type='boundary'):
        self.start = start_pos
        self.end = end_pos
        self.color = color
        self.type = type  # e.g. 'parking', 'no_cross', etc.

    def draw(self, surface):
        pygame.draw.line(surface, self.color, self.start, self.end, 3)

    def is_near_point(self, x, y, threshold=5):
        # Check if point (x, y) is close to the line segment
        px, py = x, y
        x1, y1 = self.start
        x2, y2 = self.end

        # Calculate distance from point to line segment
        line_mag = math.hypot(x2 - x1, y2 - y1)
        if line_mag < 1e-6:
            return False

        u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)
        u = max(0, min(1, u))
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)

        dist = math.hypot(px - ix, py - iy)
        return dist <= threshold


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
    elif mode == 'auto':
        car.cast_sensor(obstacles, screen)
        car.move_auto(screen)


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
# Functions
# ================================


def update_logic(car, mode):
    keys = pygame.key.get_pressed()
    if mode == 'manual':
        car.move_manual(keys)
    else:
        car.move_auto(screen)

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
        draw_ui(mode)
        car.draw(screen)
        car.cast_sensor(obstacles, screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
