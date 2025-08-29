import cv2
from game import Game
from camera_utils import calculate_head_tilt_angle, both_hands, one_hand

def prepared_frame(frame):
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return rgb

def show_instructions_until_thumb(game, cap):
    while True:
        # loading camera frames
        success, frame = cap.read()
        # stopping application if no camera frame or ESC pressed
        if not success:
            print("Error with camera input")
            return True
        if cv2.waitKey(1) & 0xFF == 27:
            print("Exitting game...")
            return True
        results = game.hands.process(prepared_frame(frame))

        # checking if both hands visible
        if both_hands(results):
            return False
        
        game.main_window.show_instructions(frame)

def game_loop(game, cap):
    while cap.isOpened():
        # loading camera frames
        success, frame = cap.read()
        # stopping application if no camera frame or ESC pressed
        if not success:
            print("Error with camera input")
            return True
        if cv2.waitKey(1) & 0xFF == 27:
            print("Exitting game...")
            return True
        
        # stopping game loop if game over
        if game.is_game_over():
            return False
        
        # getting face landmarks from fame
        results_face = game.face_mesh.process(prepared_frame(frame))
        results_hands = game.hands.process(prepared_frame(frame))
        image_height, image_width, _ = frame.shape

        if results_face.multi_face_landmarks is not None:
            # getting facemarks
            players_landmarks = None
            min_distance = 100000
            for face_landmarks in results_face.multi_face_landmarks:
                dist_from_center = abs((face_landmarks.landmark[33].x + face_landmarks.landmark[263].x) / 2 - 0.5)
                if dist_from_center < min_distance:
                    players_landmarks = face_landmarks
                    min_distance = dist_from_center
            # game.draw_landmarks(frame, players_landmarks,image_width,image_height)

            # pause game mechanism
            hand_visible = one_hand(results_hands)
            if hand_visible:
                if not game.pause_start:
                    if game.paused:
                        game.paused = False
                        game.pause_start = True
                    else:
                        game.paused = True
                        game.pause_start = True
            elif not hand_visible and game.pause_start:
                game.pause_start = False

            if game.paused:
                game.main_window.print_game(game, frame)
                continue             

            # updateing game state
            if not game.paused:
                angle = calculate_head_tilt_angle(players_landmarks.landmark, image_width, image_height)
                game.update_platform(angle)
                game.update_ball()
        game.main_window.print_game(game, frame)

def game_over(game, cap):
    while True:
        # loading camera frames
        success, frame = cap.read()
        # stopping application if no camera frame or ESC pressed
        if not success:
            print("Error with camera input")
            return False
        if cv2.waitKey(1) & 0xFF == 27:
            print("Exitting game...")
            return False
        
        results = game.hands.process(prepared_frame(frame))

        # checking if both hands visible
        if both_hands(results):
            return True
        
        game.show_game_over(frame)


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    
    game = Game()

    stop = show_instructions_until_thumb(game, cap)
    if not stop:
        while True:
            game.countdown()
            stop = game_loop(game, cap)
            if stop:
                break
            if_restart = game_over(game, cap)
            if if_restart: 
                game.reset_game()
                continue
            else:
                break

    cap.release()
    cv2.destroyAllWindows()
