import numpy as np
import mediapipe as mp
import cv2
import time
import random
from window import GameWindow
from camera_utils import calculate_head_tilt_angle, is_mouth_open, is_hand_open

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
        self.paused = False
        self.MOUTH_OPEN_THRESHOLD = 0.35
        self.mouth_detection_enabled = False

        # mediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=3)
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
        self.mp_drawing = mp.solutions.drawing_utils

        # visual game object initializtion
        self.ball = Ball()
        self.rectangles = [Rectangle(10 + i * 60, 55 * j ) for i in range(self.block_column_number) for j in range(1,self.block_row_number)]

        self.main_window = GameWindow()

    def show_instructions_until_thumb(self, cap):
        while True:

            success, frame = cap.read()
            if not success:
                continue

            self.main_window.show_instructions(frame)

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = self.hands.process(rgb)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    open_hands = 0
                    for hand_landmarks in results.multi_hand_landmarks:
                        if is_hand_open(hand_landmarks):
                            open_hands += 1
                    if open_hands >= 2:
                        # cv2.putText(self.window, "START", (60, 360),
                        #             cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                        # cv2.imshow("BRICK BREAKER GAME", self.window)
                        # cv2.waitKey(1000)
                        self.main_window.countdown()
                        return  
            # else:
            #     cv2.putText(self.window, "POKAZ OBIE DLONIE ABY ROZPOCZAC", (60, 360),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
                
            # cv2.imshow("BRICK BREAKER GAME", self.window)
            self.main_window.show_instructions(frame)
            if cv2.waitKey(1) & 0xFF == 27:
                cv2.destroyAllWindows()
                exit()

    def frame_to_game_move(self, frame):
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(image_rgb)
        image_height, image_width, _ = frame.shape

        angle = 0
        direction = "prosto"

        if results.multi_face_landmarks is not None:
            players_landmarks = None
            min_distance = 100000
            for face_landmarks in results.multi_face_landmarks:
                dist_from_center = abs((face_landmarks.landmark[33].x + face_landmarks.landmark[263].x) / 2 - 0.5)
                if dist_from_center < min_distance:
                    players_landmarks = face_landmarks
                    min_distance = dist_from_center

            self.mp_drawing.draw_landmarks(frame, players_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS,
                                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 0, 255)))
            angle = calculate_head_tilt_angle(players_landmarks.landmark, image_width, image_height)
            if self.mouth_detection_enabled and is_mouth_open(players_landmarks.landmark, image_width, image_height):
                if not self.paused:
                    self.paused = True
                    print("PAUZA")
            else:
                if self.mouth_detection_enabled and self.paused:
                    self.paused = False
                    print("WZNOWIENIE GRY")


            direction = "lewo" if angle < -3 else "prawo" if angle > 3 else "prosto"
            angle_display = int(abs(angle))
            print(f"Przechylenie: {direction}, Kąt: {angle_display}°")

            # platform movement
            if direction == "prawo":
                platform_speed = max(10, abs(angle))
            elif direction == "lewo":
                platform_speed = -max(10, abs(angle))
            else:
                platform_speed = 0

            self.platform_pos += platform_speed / 1.2
            self.platform_pos = max(0, min(self.main_window.platform_area_width - self.platform_width, self.platform_pos))

            if not self.paused:
                self.update_ball()
        self.main_window.print_game(self, frame)

    def update_ball(self):
        # global score, game_over, game_started, start_time, end_time

        if not self.game_started:
            self.game_started = True
            self.start_time = time.time()

        self.ball.x += self.ball.dx
        self.ball.y += self.ball.dy

        # collisions - ball and border
        if self.ball.x - self.ball.radius <= 0 or self.ball.x + self.ball.radius >= 720:
            self.ball.dx = -self.ball.dx
        if self.ball.y - self.ball.radius <= 0:
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
        # global self.ball, rectangles, score, game_over, game_started, start_time, end_time
        self.ball = Ball()
        self.rectangles = [Rectangle(10 + i * 60, 55 * j ) for i in range(self.block_column_number) for j in range(1,self.block_row_number)]
        self.score = 0
        self.game_over = False
        self.game_started = False
        self.start_time = None
        self.end_time = None

    def is_victory(self):
        return all(not r.active for r in self.rectangles)

