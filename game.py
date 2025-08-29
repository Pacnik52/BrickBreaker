import numpy as np
import mediapipe as mp
import cv2
import time
import random
from window import GameWindow

class Ball:
    def __init__(self):
        self.radius = 10
        self.x = 360
        self.y = 400
        self.dx = 5
        self.dy = -5

class Rectangle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 20
        self.active = True
        self.color = random.choice([
            (255, 0, 0),     # red
            (0, 255, 0),     # green
            (0, 0, 255),     # blue
            (255, 255, 0),   # yellow
            (255, 0, 255),   # purple
            (0, 255, 255)    # turquoise 
        ])

class Game:
    def __init__(self):
        self.game_over = False
        self.game_started = False
        self.start_time = None
        self.end_time = None
        self.score = 0
        self.block_row_number = 6
        self.block_column_number = 12

        self.platform_pos = 320
        self.platform_speed = 0
        self.platform_width = 80
        self.platform_height = 20

        # game parameters
        self.pause_start = False
        self.paused = False

        # mediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=3)
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
        self.mp_drawing = mp.solutions.drawing_utils

        # visual game object initializtion
        self.ball = Ball()
        self.rectangles = [Rectangle(10 + i * 60, 10 + (55 * (j-1)) ) for i in range(self.block_column_number) for j in range(1,self.block_row_number)]

        self.main_window = GameWindow()

    def draw_landmarks(self, frame, landmarks, image_width, image_height):
        left_eye = landmarks.landmark[33]
        right_eye = landmarks.landmark[263]

        left_eye_px = (int(left_eye.x * image_width), int(left_eye.y * image_height))
        right_eye_px = (int(right_eye.x * image_width), int(right_eye.y * image_height))

        cv2.circle(frame, left_eye_px, 4, (0, 255, 0), -1)
        cv2.circle(frame, right_eye_px, 4, (0, 255, 0), -1)

        dx = right_eye_px[0] - left_eye_px[0]
        dy = right_eye_px[1] - left_eye_px[1]

        length = (dx**2 + dy**2) ** 0.5
        if length == 0:
            length = 1
        dx /= length
        dy /= length

        extend = 10000
        pt1 = (int(left_eye_px[0] - dx * extend), int(left_eye_px[1] - dy * extend))
        pt2 = (int(right_eye_px[0] + dx * extend), int(right_eye_px[1] + dy * extend))

        cv2.line(frame, pt1, pt2, (0, 255, 0), 5)
    
    def update_platform(self, angle):
        direction = "L" if angle < -3 else "R" if angle > 3 else "S"

        # platform movement
        if direction == "R":
            platform_speed = max(10, abs(angle))
        elif direction == "L":
            platform_speed = -max(10, abs(angle))
        else:
            platform_speed = 0
        self.platform_pos += platform_speed / 1.2
        self.platform_pos = max(0, min(self.main_window.platform_area_width - self.platform_width, self.platform_pos))

    def update_ball(self):

        if not self.game_started:
            self.game_started = True
            self.start_time = time.time()

        self.ball.x += self.ball.dx
        self.ball.y += self.ball.dy

        # collisions - ball and border
        if self.ball.x - self.ball.radius <= 0:
            self.ball.x = self.ball.radius
            self.ball.dx = -self.ball.dx

        if self.ball.x + self.ball.radius >= 720:
            self.ball.x = 720 - self.ball.radius
            self.ball.dx = -self.ball.dx

        if self.ball.y - self.ball.radius <= 0:
            self.ball.y = self.ball.radius
            self.ball.dy = -self.ball.dy

        # collisions - self.ball and diezone
        if self.ball.y + self.ball.radius >= 500:
            self.end_time = time.time()
            self.game_over = True
            return

        # collisions - self.ball and platform
        if (460 >= self.ball.y + self.ball.radius >= 450 and
                self.platform_pos <= self.ball.x <= self.platform_pos + self.platform_width):
            self.ball.dy = -abs(self.ball.dy)
            hit_pos = ((self.ball.x - self.platform_pos) / self.platform_width) * 2 - 1
            self.ball.dx = hit_pos * 5


        # collisions - self.ball and bricks
        for rect in self.rectangles:
            if rect.active:
                if (rect.x - self.ball.radius <= self.ball.x <= rect.x + rect.width + self.ball.radius and
                    rect.y - self.ball.radius <= self.ball.y <= rect.y + rect.height + self.ball.radius):

                    x_collision = abs(self.ball.x - rect.x) if self.ball.dx > 0 else abs(self.ball.x - (rect.x + rect.width))
                    y_collision = abs(self.ball.y - rect.y) if self.ball.dy > 0 else abs(self.ball.y - (rect.y + rect.height))
                    min_collision = min(x_collision, y_collision)

                    if min_collision == x_collision:
                        self.ball.dx = -self.ball.dx
                    if min_collision == y_collision:
                        self.ball.dy = -self.ball.dy

                    rect.active = False
                    self.score += 10

        if all(not r.active for r in self.rectangles):
            self.end_time = time.time()
            self.game_over = True
    
    def countdown(self):
        self.main_window.countdown()

    def show_game_over(self, frame):
        return self.main_window.print_game_over(self, frame)

    def is_game_over(self):
        return self.game_over
    
    def print_game_over(self):
        self.main_window.print_game_over(self)

    def get_score(self):
        return self.score

    def get_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def reset_game(self):
        self.ball = Ball()
        self.rectangles = [Rectangle(10 + i * 60, 10 + (55 * (j - 1)) ) for i in range(self.block_column_number) for j in range(1,self.block_row_number)]
        self.score = 0
        self.game_over = False
        self.game_started = False
        self.start_time = None
        self.end_time = None
        self.platform_pos = 320

    def is_victory(self):
        return all(not r.active for r in self.rectangles)

