import cv2
import mediapipe as mp
import numpy as np
from camera_utils import calculate_head_tilt_angle, is_mouth_open, is_hand_open

class GameWindow:
    def __init__(self):
        # platfrm parameters


        # game window parameters
        self.main_height = 480
        self.platform_area_width = 720  # platform moving area
        self.camera_frame_size = (240, 180)  # camera output frame size
        self.main_width = self.platform_area_width + self.camera_frame_size[0] + 20  # 720 + 240 + 20 = 980

        self.window = np.ones((self.main_height, self.main_width, 3), dtype=np.uint8) * 30

    def show_instructions(self,frame):
        self.reset_window()
        instructions = [
                "ZASADY GRY:",
                "- Steruj platforma przechylajac glowe",
                "- Im mocniej przechylisz, tym szybciej sie porusza",
                "- Gra konczy sie, gdy pilka spadnie",
                "- Pauza: otwarcie ust",
                "- START: pokaz 2 dlonie do kamery"
            ]
        for i, line in enumerate(instructions):
            cv2.putText(self.window, line, (60, 100 + i * 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cam_small = cv2.resize(frame, (240, 180))
        self.window[10:190, self.main_width - 250:self.main_width - 10] = cam_small
        cv2.imshow("BRICK BREAKER GAME", self.window)

    def countdown(self):
        for i in range(3, 0, -1):
            self.reset_window()
            cv2.putText(self.window, f"{i}", (self.main_width // 2 - 30, self.main_height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
            cv2.imshow("BRICK BREAKER GAME", self.window)
            cv2.waitKey(1000)

        # print START
        self.window = np.ones((self.main_height, self.main_width, 3), dtype=np.uint8) * 30
        cv2.putText(self.window, "START!", (self.main_width // 2 - 100, self.main_height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
        cv2.imshow("BRICK BREAKER GAME", self.window)
        # cv2.waitKey(1000)
        # cv2.imshow("BRICK BREAKER GAME", self.window)

    def print_game(self, game, frame):
            # main game window
            self.window = np.ones((self.main_height, self.main_width, 3), dtype=np.uint8) * 30
            cv2.rectangle(self.window, (0, 0), (self.platform_area_width - 1, self.main_height - 1), (255, 255, 255), 2)

            # platform print
            cv2.rectangle(self.window,
                        (int(game.platform_pos), self.main_height - game.platform_height - 10),
                        (int(game.platform_pos + game.platform_width), self.main_height - 10),
                        (0, 255, 0), -1)

            # camera print
            cam_small = cv2.resize(self.window, self.camera_frame_size)
            cam_h, cam_w = cam_small.shape[:2]

            # # text print
            # cam_text = f"{direction.upper()}, {int(abs(game.angle))}"
            # if game.paused:
            #     cam_text += "  |  PAUZA"

            # position
            # text_x = self.platform_area_width + 10
            # text_y = 10 + cam_h + 30

            # cv2.putText(self.window, cam_text, (text_x, text_y),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # cam_h, cam_w = cam_small.shape[:2]
            # frame[10:10 + cam_h, self.platform_area_width + 10:self.platform_area_width + 10 + cam_w] = cam_small
            # cam_small = cv2.resize(frame, cam_small.shape[:2])
            # self.window[10:190, self.main_width - 250:self.main_width - 10] = cam_small
            cam_small = cv2.resize(frame, self.camera_frame_size)
            self.window[10:10 + cam_h, self.platform_area_width + 10:self.platform_area_width + 10 + cam_w] = cam_small

            # game objects
            self.draw_game_objects(game)

            if game.paused:
                cv2.putText(cam_small, "PAUZA", (50, 250),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)

            # show
            cv2.imshow("BRICK BREAKER GAME", self.window)

    def draw_game_objects(self, game):
        # draw ball
        cv2.circle(self.window, (int(game.ball.x), int(game.ball.y)), game.ball.radius, (255, 255, 0), -1)

        # draw bricks
        for rect in game.rectangles:
            if rect.active:
                cv2.rectangle(self.window,
                            (int(rect.x), int(rect.y)),
                            (int(rect.x + rect.width), int(rect.y + rect.height)),
                            rect.color, -1)

        # draw score
        cv2.putText(self.window, f'Score: {game.score}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    def print_game_over(self, game):
        if game.is_victory():
            message = f"WYGRALES! Wynik: {game.score} | Czas: {game.get_duration():.1f}s"
        else:
            message = f"KONIEC GRY. Wynik: {game.score} | Czas: {game.get_duration():.1f}s"

        cv2.putText(self.window, message, (50, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 3)
        while True:
            self.reset_window()
            duration = game.get_duration()
            final_score = game.score
            summary = f'KONIEC GRY! Punkty: {final_score}, Czas: {duration:.1f} s'
            cv2.putText(self.window, summary, (50, self.main_height // 2 - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(self.window, "Nacisnij R aby zagrac ponownie", (50, self.main_height // 2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(self.window, "lub Q aby zakonczyc", (50, self.main_height // 2 + 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("BRICK BREAKER GAME", self.window)
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q'):
                # cap.release()
                cv2.destroyAllWindows()
                exit()
            elif key == ord('r'):
                # from game import reset_game
                game.reset_game()
                self.countdown()
                platform_pos = 320
                break 
    
    def reset_window(self):
        self.window = np.ones((self.main_height, self.main_width, 3), dtype=np.uint8) * 30