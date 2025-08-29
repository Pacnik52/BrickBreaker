import cv2
from game import Game
from camera_utils import calculate_head_tilt_angle, is_mouth_open, is_hand_open

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

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = game.hands.process(rgb)

        # checking if both hands visible
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                open_hands = 0
                for hand_landmarks in results.multi_hand_landmarks:
                    if is_hand_open(hand_landmarks):
                        open_hands += 1
                if open_hands >= 2:
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
        
        # preparing camera frame
        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results_face = game.face_mesh.process(image_rgb)
        results_hands = game.hands.process(image_rgb)
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
            game.draw_landmarks(frame, players_landmarks,image_width,image_height)
            
            # mouth opening stopping game mechanism
            if game.mouth_detection_enabled:
                if is_mouth_open(players_landmarks.landmark, image_width, image_height, MOUTH_OPEN_THRESHOLD = 0.35):
                    if not game.pause_start and not game.paused:
                        game.pause_start = True
                        print("PAUZA_ON_START")
                    elif not game.pause_start and game.paused:
                        game.pause_start = True
                        print("PAUZA_OFF_START")
                else:
                    if game.pause_start and game.paused:
                        game.paused = False
                        game.pause_start = False
                        print("PAUZA_OFF")
                    if game.pause_start and not game.paused:
                        game.paused = True
                        game.pause_start = False
                        print("PAUZA_ON")
            if game.paused:
                print("dupa")
                game.main_window.print_game(game, frame)
                return              

            # updateing game state
            angle = calculate_head_tilt_angle(players_landmarks.landmark, image_width, image_height)
            if not game.paused:
                game.update_platform(angle)
                game.update_ball()
        game.main_window.print_game(game, frame)

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
            if_restart = game.show_game_over()
            if if_restart: 
                game.reset_game()
                continue
            else: 
                break

    cap.release()
    cv2.destroyAllWindows()
