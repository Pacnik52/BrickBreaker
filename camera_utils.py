import numpy as np
import math

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

# hand gestures 
def is_hand_open(hand_landmarks):
    lm = hand_landmarks.landmark
    open_fingers = [
        lm[8].y < lm[6].y,   # pointing finger
        lm[12].y < lm[10].y, # middle finger
        lm[16].y < lm[14].y, # ring finger
        lm[20].y < lm[18].y  # pinky
    ]
    return sum(open_fingers) >= 4 # min4 open
    
def both_hands(hand_results):
    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            open_hands = 0
            for hand_landmarks in hand_results.multi_hand_landmarks:
                if is_hand_open(hand_landmarks):
                    open_hands += 1
            if open_hands >= 2:
                return True
    return False
            
def one_hand(hand_results):
    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            if is_hand_open(hand_landmarks):
                return True
    return False