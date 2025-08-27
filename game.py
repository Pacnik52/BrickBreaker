import numpy as np
import cv2
import time
import random

# game varables
game_over = False
game_started = False
start_time = None
end_time = None
score = 0
block_row_number = 6
block_column_number = 12

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

# game object initializtion
ball = Ball()
rectangles = [Rectangle(10 + i * 60, 55 * j ) for i in range(block_column_number) for j in range(1,block_row_number)]


def update_ball(platform_pos, platform_width):
    global score, game_over, game_started, start_time, end_time

    if not game_started:
        game_started = True
        start_time = time.time()

    ball.x += ball.dx
    ball.y += ball.dy

    # collisions - ball and border
    if ball.x - ball.radius <= 0 or ball.x + ball.radius >= 720:
        ball.dx = -ball.dx
    if ball.y - ball.radius <= 0:
        ball.dy = -ball.dy

    # collisions - ball and diezone
    if ball.y + ball.radius >= 500:
        end_time = time.time()
        game_over = True
        return

    # collisions - ball and platform
    if (460 >= ball.y + ball.radius >= 450 and
            platform_pos <= ball.x <= platform_pos + platform_width):
        ball.dy = -abs(ball.dy)

    # collisions - ball and bricks
    for rect in rectangles:
        if rect.active:
            if (rect.x - ball.radius <= ball.x <= rect.x + rect.width + ball.radius and
                rect.y - ball.radius <= ball.y <= rect.y + rect.height + ball.radius):

                x_collision = abs(ball.x - rect.x) if ball.dx > 0 else abs(ball.x - (rect.x + rect.width))
                y_collision = abs(ball.y - rect.y) if ball.dy > 0 else abs(ball.y - (rect.y + rect.height))
                min_collision = min(x_collision, y_collision)

                if min_collision == x_collision:
                    ball.dx = -ball.dx
                if min_collision == y_collision:
                    ball.dy = -ball.dy

                rect.active = False
                score += 10

    if all(not r.active for r in rectangles):
        end_time = time.time()
        game_over = True

def draw_game_objects(frame):
    cv2.circle(frame, (int(ball.x), int(ball.y)), ball.radius, (255, 255, 0), -1)

    for rect in rectangles:
        if rect.active:
            cv2.rectangle(frame,
                        (int(rect.x), int(rect.y)),
                        (int(rect.x + rect.width), int(rect.y + rect.height)),
                        rect.color, -1)

    cv2.putText(frame, f'Score: {score}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

def is_game_over():
    return game_over

def get_score():
    return score

def get_duration():
    if start_time and end_time:
        return end_time - start_time
    return 0

def reset_game():
    global ball, rectangles, score, game_over, game_started, start_time, end_time
    ball = Ball()
    rectangles = [Rectangle(10 + i * 60, 55 * j ) for i in range(block_column_number) for j in range(1,block_row_number)]
    score = 0
    game_over = False
    game_started = False
    start_time = None
    end_time = None

def is_victory():
    return all(not r.active for r in rectangles)

def countdown(main_width, main_height):
    for i in range(3, 0, -1):
        frame = np.ones((main_height, main_width, 3), dtype=np.uint8) * 30
        cv2.putText(frame, f"{i}", (main_width // 2 - 30, main_height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
        cv2.imshow("BRICK BREAKER GAME", frame)
        cv2.waitKey(1000)

    # print START
    frame = np.ones((main_height, main_width, 3), dtype=np.uint8) * 30
    cv2.putText(frame, "START!", (main_width // 2 - 100, main_height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
    cv2.imshow("BRICK BREAKER GAME", frame)
    cv2.waitKey(1000)

