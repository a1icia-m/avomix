"""
Vertical volume bar: up = louder, down = quieter.
Uses same confirm-then-lock logic as DJ wheel (only changes while hovering/editing).
"""
import cv2


class VolumeBar:
    """
    Vertical bar for deck volume. Volume only updates while 'editing';
    pinch (click/snap) over the bar to enter editing, pinch again to lock.
    """

    def __init__(self, x, y, width, height, side, song_selector):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.side = side
        self.selector = song_selector
        self.hand = "Left" if side == "left" else "Right"
        self.is_editing_volume = False
        self._was_pinching = False

    def _in_bar_region(self, pos):
        """True if pos is inside the vertical bar rect (generous margin for easy targeting)."""
        if pos is None:
            return False
        margin_x = 25  # wide horizontal margin so bar is easy to hit
        margin_y = 15
        return (
            self.x - margin_x <= pos[0] <= self.x + self.width + margin_x
            and self.y - margin_y <= pos[1] <= self.y + self.height + margin_y
        )

    def _y_to_volume(self, fy):
        """Map finger y to volume 0.0 (bottom) .. 1.0 (top)."""
        # top of bar = self.y = volume 1.0, bottom = self.y + height = volume 0.0
        t = (self.y + self.height - fy) / self.height
        return max(0.0, min(1.0, t))

    def update(self, hand, finger_pos):
        """
        Call each frame. Pinch down over bar when locked → enter editing.
        While editing, finger y sets volume. Pinch down again → lock.
        """
        if hand != self.hand:
            return

        is_pinching = finger_pos is not None
        finger_in = finger_pos is not None and self._in_bar_region(finger_pos)

        if not is_pinching:
            self._was_pinching = False
            return

        pinch_down = is_pinching and not self._was_pinching
        self._was_pinching = True

        if pinch_down:
            if self.is_editing_volume:
                self.is_editing_volume = False
                return
            else:
                if finger_in:
                    self.is_editing_volume = True

        if not self.is_editing_volume or not finger_in or finger_pos is None:
            return

        vol = self._y_to_volume(finger_pos[1])
        self.selector.set_volume(self.side, vol)

    def draw(self, frame):
        """
        Draw vertical bar. Interior is transparent; only a colored level strip
        is drawn, which fades from almost clear (low volume) to bright green
        (high volume). Border is brighter while editing.
        """
        vol = self.selector.get_volume(self.side)
        fill_h = int(self.height * vol)

        # Outer border
        track_color = (200, 200, 200) if self.is_editing_volume else (100, 100, 100)
        cv2.rectangle(
            frame,
            (self.x, self.y),
            (self.x + self.width, self.y + self.height),
            track_color,
            2,
        )

        # Filled level (from bottom up) – no background fill, so underlying image shows through
        if fill_h > 0:
            fill_y = self.y + self.height - fill_h
            # Color intensity scales with volume: low = dark, high = bright green
            g = int(80 + 150 * vol)
            color = (40, g, 60)
            cv2.rectangle(
                frame,
                (self.x + 3, fill_y),
                (self.x + self.width - 3, self.y + self.height - 3),
                color,
                -1,
            )
