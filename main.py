import cv2
from hand_tracking import HandTracker, draw_hand_skeleton
from song_selector import SongSelector
from ui import PlayButton

def main():
    tracker = HandTracker()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Camera not found.")
        return

    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read from camera.")
        return

    height, width, _ = frame.shape

    def_left = "patty_cake"
    def_right = "ctmn"

    song_selector = SongSelector()
    song_selector.select("left", def_left)
    song_selector.select("right", def_right)

    # Play/pause buttons: left and right
    py = 2 * height // 3
    left_btn = PlayButton(width // 4 - 30, py, 100, 100, song_selector, "left")
    right_btn = PlayButton(3 * width // 4 - 70, py, 100, 100, song_selector, "right")
    buttons = [left_btn, right_btn]

    print("DJ Hand Tracking Started. Press 'q' to exit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Ignoring empty camera frame.")
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tracker.detect_async(rgb_frame)

            result = tracker.get_latest_result()

            frame = draw_hand_skeleton(frame, tracker, result)

            for hand in ["Left", "Right"]:
                pinch_pos = tracker.pinch_pos[hand]
                # Flip to display coords for hit detection
                if pinch_pos:
                    pinch_pos = (width - 1 - pinch_pos[0], pinch_pos[1])

                for button in buttons:
                    if tracker.state[hand] == 1:
                        button.update(hand, pinch_pos)
                    else:
                        button.pinched[hand] = False
            
            reversed_frame = cv2.flip(frame, 1)

            for button in buttons:
                button.draw(reversed_frame)

            cv2.imshow('CV DJ Set', reversed_frame)

            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        song_selector.close()
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
