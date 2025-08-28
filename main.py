import cv2
import time
from game import Game


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    
    game = Game()

    game.show_instructions_until_thumb(cap)
    # time.sleep(2)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # getting next camera frame
        frame = cv2.flip(frame, 1)
        game.frame_to_game_move(frame)

        # current game prning every camera frame
        if game.is_game_over():
            game.print_game_over()

        # closing on Esc
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
