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

# mouth opening
def is_mouth_open(landmarks, image_width, image_height, MOUTH_OPEN_THRESHOLD):
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