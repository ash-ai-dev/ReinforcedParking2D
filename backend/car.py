
import pygame
import sys
import math
import random

from obstacle import *

# Screen setup
WIDTH, HEIGHT = 800, 600  # Wider screen
GAME_WIDTH = 600           # Game area

# Load car sprite
car_image = pygame.image.load("car.png")
car_image = pygame.transform.scale(car_image, (60, 30))

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
        # Draw sensor circle around the car
        sensor_radius = 150
        pygame.draw.circle(surface, (200, 200, 200), (int(self.x), int(self.y)), sensor_radius, 1)

        # Draw the car image rotated
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

    def cast_sensor_circle(self, surface, radius=80, visualize=True):
        yellow_threshold = 20
        yellow_count = 0
        points = []

        for dx in range(-radius, radius):
            for dy in range(-radius, radius):
                if dx**2 + dy**2 <= radius**2:
                    sx = int(self.x + dx)
                    sy = int(self.y + dy)

                    if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                        r, g, b = surface.get_at((sx, sy))[:3]
                        if r > 200 and g > 200 and b < 100:
                            yellow_count += 1
                            points.append((sx, sy))

        if visualize:
            # Create a transparent surface for the sensor circle
            overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (255, 255, 0, 100), (radius, radius), radius)
            surface.blit(overlay, (int(self.x - radius), int(self.y - radius)))

            for px, py in points:
                pygame.draw.circle(surface, (255, 255, 0), (px, py), 2)

        return yellow_count >= yellow_threshold


        
    def cast_sensor(self, obstacles, surface):
        sensor_configs = [
            ("Front Left", self.angle - math.pi / 6, (0, 255, 0)),
            ("Front Center", self.angle, (0, 255, 0)),
            ("Front Right", self.angle + math.pi / 6, (0, 255, 0)),
            ("Rear Left", self.angle + math.pi - math.pi / 6, (0, 200, 255)),
            ("Rear Center", self.angle + math.pi, (0, 200, 255)),
            ("Rear Right", self.angle + math.pi + math.pi / 6, (0, 200, 255)),
            ("Side Left", self.angle - math.pi / 2, (255, 165, 0)),  # Orange
            ("Side Right", self.angle + math.pi / 2, (255, 165, 0))
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

                    elif isinstance(obj, LineSegment):
                        if segments_intersect((self.x, self.y), (sx, sy), obj.start, obj.end):
                            hit = True
                            break
                
                if hit:
                    self.sensor_data[label] = dist
                    if dist < 80:
                        color = (255, 0, 0)
                    elif dist < 120:
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
            if self.cast_sensor_circle(surface):
                pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), 10)
                self.auto_state = "parking"
                self.speed = 0
                print("Yellow lines detected: switching to parking mode")
                return

            self.speed = 2
            front = self.sensor_data.get("Front Center", 200)
            left = self.sensor_data.get("Front Left", 200)
            right = self.sensor_data.get("Front Right", 200)

            if front < 80:
                self.speed = 0
                self.steering_angle = math.radians(-25 if left > right else 25)
                print("Obstacle ahead! Turning to avoid")
            elif left < 50:
                self.steering_angle = math.radians(20)
                print("Obstacle on left! Steering right")
            elif right < 50:
                self.steering_angle = math.radians(-20)
                print("Obstacle on right! Steering left")
            left_side = self.sensor_data.get("Side Left", 200)
            right_side = self.sensor_data.get("Side Right", 200)

            # Avoid tight squeeze between two walls or obstacles
            if left_side < 40 and right_side < 40:
                self.speed = 0
                self.steering_angle = math.radians(30 if left_side > right_side else -30)
                print("Tight squeeze! Steering sharply to avoid.")
            elif left_side < 50:
                self.steering_angle = math.radians(20)
                print("Wall too close on left! Steering right")
            elif right_side < 50:
                self.steering_angle = math.radians(-20)
                print("Wall too close on right! Steering left")

            else:
                self.steering_angle *= 0.9
                print("Clear path, going forward")

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

    def execute_parking_maneuver(self):
        # Constants
        REVERSE_SPEED = -1.5
        FORWARD_SPEED = 2.0
        PARKING_ANGLE = math.radians(28)
        CENTERING_ANGLE = math.radians(5)
        
        REAR_CLEARANCE = 30
        SIDE_CLEARANCE = 40
        LINE_DANGER_THRESHOLD = 25
        SUCCESS_TIMER_LIMIT = 40
        RECOVERY_FRAMES = 25 

        # Sensor readings
        rear_center = self.sensor_data.get("Rear Center", 200)
        side_left = self.sensor_data.get("Side Left", 200)
        side_right = self.sensor_data.get("Side Right", 200)

        # Are we inside the parking spot?
        in_spot = self.cast_sensor_circle(surface=pygame.display.get_surface(), radius=70, visualize=False)

        # Recovery mode: sharply turn out of danger
        if getattr(self, "recovery_timer", 0) > 0:
            self.recovery_timer -= 1
            self.parked_timer = 0
            self.speed = FORWARD_SPEED
            self.steering_angle = self.recovery_steering_angle
            print(f"🛠️ Recovering from danger... Frames left: {self.recovery_timer}")
            return

        # Trigger recovery if too close to yellow lines
        if side_left < LINE_DANGER_THRESHOLD or side_right < LINE_DANGER_THRESHOLD:
            self.recovery_timer = RECOVERY_FRAMES
            if side_left < side_right:
                self.recovery_steering_angle = PARKING_ANGLE  # Steer left
            else:
                self.recovery_steering_angle = -PARKING_ANGLE # Steer right
            print(f"Too close to line! Initiating recovery. Sides: {side_left}, {side_right}")
            return  # Start recovery next frame

        # Check if well parked
        if in_spot and rear_center < REAR_CLEARANCE and side_left > SIDE_CLEARANCE and side_right > SIDE_CLEARANCE:
            self.parked_timer += 1
            self.speed = 0
            self.steering_angle = 0
            print(f"Holding... Parked timer: {self.parked_timer}")
        
        else:
            self.parked_timer = 0
            self.speed = REVERSE_SPEED

            # Steering to favor avoiding closer wall
            if side_left < side_right:
                self.steering_angle = -PARKING_ANGLE  # Steer right
            elif side_right < side_left:
                self.steering_angle = PARKING_ANGLE   # Steer left
            else:
                self.steering_angle = CENTERING_ANGLE

            print(f"Parking... Reverse. Rear: {rear_center}, Sides: {side_left}, {side_right}")

        # Success
        if self.parked_timer >= SUCCESS_TIMER_LIMIT:
            self.speed = 0
            self.steering_angle = 0
            self.auto_state = "parked"
            print("Successfully parked!")
