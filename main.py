import cv2
from hand_tracking import HandTracker, draw_hand_skeleton
from song_selector import SongSelector
from ui import PlayButton, StemButton
from dj_wheel import DJWheel, DEFAULT_RADIUS
from volume_bar import VolumeBar

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

    # Song folder names under songs/ (each must have bass.mp3, drums.mp3, other.mp3, vocals.mp3)
    def_left = "no pole"
    def_right = "where"

    song_selector = SongSelector()
    song_selector.select("left", def_left)
    song_selector.select("right", def_right)

    # Play/pause buttons: left and right
    py = 2 * height // 3
    left_btn = PlayButton(width // 4 - 30, py, 100, 100, song_selector, "left")
    right_btn = PlayButton(3 * width // 4 - 70, py, 100, 100, song_selector, "right")
    buttons = [left_btn, right_btn]

    # DJ wheels: scrub by angular finger position (left hand = left deck, right hand = right deck)
    wheel_radius = DEFAULT_RADIUS
    wheel_y = py - 140
    left_wheel = DJWheel(width // 4, wheel_y, wheel_radius, "left", song_selector)
    right_wheel = DJWheel(3 * width // 4, wheel_y, wheel_radius, "right", song_selector)
    wheels = [left_wheel, right_wheel]

    # Stem buttons under each wheel (bass, drums, other, vocals)
    stem_btn_w, stem_btn_h = 42, 26
    stem_y = wheel_y + wheel_radius + 14
    stem_labels = ["bass", "drums", "other", "vocals"]
    stem_buttons = []
    for side, cx in [("left", width // 4), ("right", 3 * width // 4)]:
        total_w = 4 * stem_btn_w
        start_x = cx - total_w // 2 + stem_btn_w // 2
        for i, label in enumerate(stem_labels):
            bx = start_x + i * stem_btn_w - stem_btn_w // 2
            stem_buttons.append(
                StemButton(bx, stem_y, stem_btn_w, stem_btn_h, song_selector, side, i, label)
            )

    # Vertical volume bars: left bar left of left stem buttons, right bar right of right stem buttons
    bar_w, bar_h = 24, 100
    stem_block_half = 2 * stem_btn_w  # half-width of 4 buttons
    left_bar_x = width // 4 - stem_block_half - 12 - bar_w
    right_bar_x = 3 * width // 4 + stem_block_half + 12
    volume_bars = [
        VolumeBar(left_bar_x, stem_y - 10, bar_w, bar_h, "left", song_selector),
        VolumeBar(right_bar_x, stem_y - 10, bar_w, bar_h, "right", song_selector),
    ]

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
                for sb in stem_buttons:
                    if tracker.state[hand] == 1:
                        sb.update(hand, pinch_pos)
                    else:
                        sb.pinched[hand] = False
                # DJ wheel: scrub by angular finger position when pinching
                finger_pos = pinch_pos if (tracker.state[hand] == 1 and pinch_pos) else None
                for wheel in wheels:
                    wheel.update(hand, finger_pos)
                for vbar in volume_bars:
                    vbar.update(hand, finger_pos)

            reversed_frame = cv2.flip(frame, 1)

            for button in buttons:
                button.draw(reversed_frame)
            for wheel in wheels:
                wheel.draw(reversed_frame)
            for sb in stem_buttons:
                sb.draw(reversed_frame)
            for vbar in volume_bars:
                vbar.draw(reversed_frame)

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
