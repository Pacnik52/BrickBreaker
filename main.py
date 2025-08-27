import cv2
import mediapipe as mp
import numpy as np
import math
import time
from game import draw_game_objects, update_ball, is_game_over, is_victory, get_score, get_duration, countdown

# mediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=3)
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# head tilt
def calculate_head_tilt_angle(landmarks, image_width, image_height):
    left_eye = landmarks[33]
    right_eye = landmarks[263]
    x1, y1 = int(left_eye.x * image_width), int(left_eye.y * image_height)
    x2, y2 = int(right_eye.x * image_width), int(right_eye.y * image_height)
    delta_y = y2 - y1
    delta_x = x2 - x1
    angle_rad = math.atan2(delta_y, delta_x)
    return math.degrees(angle_rad)

# mouth opening
def is_mouth_open(landmarks, image_width, image_height):
    top_lip = landmarks[13]
    bottom_lip = landmarks[14]
    left_lip = landmarks[78]
    right_lip = landmarks[308]

    top = np.array([top_lip.x * image_width, top_lip.y * image_height])
    bottom = np.array([bottom_lip.x * image_width, bottom_lip.y * image_height])
    left = np.array([left_lip.x * image_width, left_lip.y * image_height])
    right = np.array([right_lip.x * image_width, right_lip.y * image_height])

    # mouth opening sizes up to bottom and left to right
    vertical = np.linalg.norm(top - bottom)
    horizontal = np.linalg.norm(left - right)
    # mar
    mar = vertical / horizontal if horizontal != 0 else 0
    return mar > MOUTH_OPEN_THRESHOLD  

# hand gestures 
def is_hand_open(hand_landmarks):
    lm = hand_landmarks.landmark
    open_fingers = [
        lm[8].y < lm[6].y,   # pointing finger
        lm[12].y < lm[10].y, # middle finger
        lm[16].y < lm[14].y, # ring finger
        lm[20].y < lm[18].y  # pinky
    ]
    return sum(open_fingers) >= 3 # min3 open

def show_instructions_until_thumb(cap, main_width, main_height):
    mp_drawing = mp.solutions.drawing_utils
    while True:
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        frame_height, frame_width = frame.shape[:2]
        window = np.ones((main_height, main_width, 3), dtype=np.uint8) * 30

        instructions = [
            "ZASADY GRY:",
            "- Steruj platforma przechylajac glowe",
            "- Im mocniej przechylisz, tym szybciej sie porusza",
            "- Gra konczy sie, gdy pilka spadnie",
            "- Pauza: otwarcie ust",
            "- START: pokaz 2 dlonie do kamery"
        ]
        for i, line in enumerate(instructions):
            cv2.putText(window, line, (60, 100 + i * 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cam_small = cv2.resize(frame, (240, 180))
        window[10:190, main_width - 250:main_width - 10] = cam_small

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                open_hands = 0
                for hand_landmarks in results.multi_hand_landmarks:
                    if is_hand_open(hand_landmarks):
                        open_hands += 1
                if open_hands >= 2:
                    cv2.putText(window, "START", (60, 360),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                    cv2.imshow("BRICK BREAKER GAME", window)
                    cv2.waitKey(1000)
                    return  
        else:
            cv2.putText(window, "POKAZ OBIE DLONIE ABY ROZPOCZAC", (60, 360),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)

        cv2.imshow("BRICK BREAKER GAME", window)
        if cv2.waitKey(1) & 0xFF == 27:
            cv2.destroyAllWindows()
            exit()

cap = cv2.VideoCapture(0)

# game parameters
paused = False
MOUTH_OPEN_THRESHOLD = 0.35
mouth_detection_enabled = False

# platfrm parameters
platform_pos = 320
platform_speed = 0
platform_width = 80
platform_height = 20

# game window parameters
main_height = 480
platform_area_width = 720  # platform moving area
camera_frame_size = (240, 180)  # camera output frame size
main_width = platform_area_width + camera_frame_size[0] + 20  # 720 + 240 + 20 = 980

show_instructions_until_thumb(cap, main_width, main_height)
countdown(main_width, main_height)
time.sleep(2)
mouth_detection_enabled = True

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # camera
    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image_rgb)
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

        mp_drawing.draw_landmarks(frame, players_landmarks, mp_face_mesh.FACEMESH_CONTOURS,
                                  landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 0, 255)))
        angle = calculate_head_tilt_angle(players_landmarks.landmark, image_width, image_height)
        if mouth_detection_enabled and is_mouth_open(players_landmarks.landmark, image_width, image_height):
            if not paused:
                paused = True
                print("PAUZA")
        else:
            if mouth_detection_enabled and paused:
                paused = False
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

        platform_pos += platform_speed / 1.2
        platform_pos = max(0, min(platform_area_width - platform_width, platform_pos))

        if not paused:
            update_ball(platform_pos, platform_width)


    if is_game_over():
        duration = get_duration()
        if is_victory():
            message = f"WYGRALES! Wynik: {get_score()} | Czas: {duration:.1f}s"
        else:
            message = f"KONIEC GRY. Wynik: {get_score()} | Czas: {duration:.1f}s"

        cv2.putText(main_frame, message, (50, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 3)
        while True:
            main_frame = np.ones((main_height, main_width, 3), dtype=np.uint8) * 30
            duration = get_duration()
            final_score = get_score()
            summary = f'KONIEC GRY! Punkty: {final_score}, Czas: {duration:.1f} s'
            cv2.putText(main_frame, summary, (50, main_height // 2 - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(main_frame, "Nacisnij R aby zagrac ponownie", (50, main_height // 2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(main_frame, "lub Q aby zakonczyc", (50, main_height // 2 + 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("BRICK BREAKER GAME", main_frame)
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                exit()
            elif key == ord('r'):
                from game import reset_game
                reset_game()
                platform_pos = 320
                break 

    # main game window
    main_frame = np.ones((main_height, main_width, 3), dtype=np.uint8) * 30
    cv2.rectangle(main_frame, (0, 0), (platform_area_width - 1, main_height - 1), (255, 255, 255), 2)

    # platform print
    cv2.rectangle(main_frame,
                  (int(platform_pos), main_height - platform_height - 10),
                  (int(platform_pos + platform_width), main_height - 10),
                  (0, 255, 0), -1)

    # camera print
    cam_small = cv2.resize(frame, camera_frame_size)
    cam_h, cam_w = cam_small.shape[:2]

    # text print
    cam_text = f"{direction.upper()}, {int(abs(angle))}"
    if paused:
        cam_text += "  |  PAUZA"

    # position
    text_x = platform_area_width + 10
    text_y = 10 + cam_h + 30

    cv2.putText(main_frame, cam_text, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cam_h, cam_w = cam_small.shape[:2]
    main_frame[10:10 + cam_h, platform_area_width + 10:platform_area_width + 10 + cam_w] = cam_small

    # game objects
    draw_game_objects(main_frame)

    if paused:
        cv2.putText(cam_small, "PAUZA", (50, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)


    # show
    cv2.imshow("BRICK BREAKER GAME", main_frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break


cap.release()
cv2.destroyAllWindows()
