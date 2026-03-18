"""
DJ wheel UI: scrub track position by angular hand/finger position.
Left hand scrubs left deck; right hand scrubs right deck.
"""
import cv2
import numpy as np


# Default radius (larger wheel)
DEFAULT_RADIUS = 88


class DJWheel:
    """
    Wheel that shows track progress. Position is only updated while 'editing';
    a click/snap (pinch) confirms and locks the value. Another pinch over the
    wheel re-enters editing.
    """

    def __init__(self, x, y, radius, side, song_selector):
        self.x = x
        self.y = y
        self.radius = radius
        self.side = side  # "left" or "right"
        self.selector = song_selector
        self.hand = "Left" if side == "left" else "Right"
        # Confirm-then-lock: True = hand can change position, False = value frozen
        self.is_editing_wheel = False
        self._was_pinching = False

    def _in_wheel_region(self, pos):
        """True if pos is inside the wheel circle (or within a small margin)."""
        if pos is None:
            return False
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return (dx * dx + dy * dy) <= (self.radius + 10) ** 2

    def _angle_to_fraction(self, angle_rad):
        """Convert angle (rad, 0=right, pi/2=down) to track fraction (0=top, clockwise)."""
        angle_deg = np.rad2deg(angle_rad)
        from_top = (angle_deg + 90) % 360  # 0 at top, 90 at right, 180 at bottom, 270 at left
        return from_top / 360.0

    def update(self, hand, finger_pos):
        """
        Call each frame with hand name and (x, y) in display coords, or None when not pinching.
        - Pinch down over wheel when locked → enter editing.
        - While editing, finger angle updates position.
        - Pinch down again (click/snap) → lock value and leave editing.
        """
        if hand != self.hand:
            return

        is_pinching = finger_pos is not None
        finger_in = finger_pos is not None and self._in_wheel_region(finger_pos)

        if not is_pinching:
            self._was_pinching = False
            return

        pinch_down = is_pinching and not self._was_pinching
        self._was_pinching = True

        if pinch_down:
            if self.is_editing_wheel:
                # Confirm: lock the current value
                self.is_editing_wheel = False
                return
            else:
                # Re-engage: enter editing only if finger is in wheel region
                if finger_in:
                    self.is_editing_wheel = True
                # fall through so position updates this frame when entering editing

        # While editing, update position from finger angle (only if finger in region)
        if not self.is_editing_wheel or not finger_in:
            return

        duration = self.selector.get_duration(self.side)
        if duration <= 0:
            return

        fx, fy = finger_pos
        dx = fx - self.x
        dy = fy - self.y
        dist = np.hypot(dx, dy)
        if dist < 15:  # ignore when finger too close to center (ambiguous angle)
            return

        angle_rad = np.arctan2(dy, dx)
        fraction = self._angle_to_fraction(angle_rad)
        pos_samples = fraction * duration
        self.selector.set_position(self.side, pos_samples)

    def draw(self, frame):
        """Draw the wheel (rim only, transparent inside) and playhead."""
        duration = self.selector.get_duration(self.side)
        if duration <= 0:
            return

        pos = self.selector.get_position(self.side)
        fraction = pos / duration  # 0.0 .. 1.0

        # Rim only: outer circle, no fill (transparent/clear inside)
        # Slightly different rim when editing (brighter) vs locked
        rim_color = (180, 180, 180) if self.is_editing_wheel else (120, 120, 120)
        cv2.circle(frame, (self.x, self.y), self.radius, rim_color, 2)
        cv2.circle(frame, (self.x, self.y), self.radius - 3, (60, 60, 60), 1)

        # Thin progress arc (outline only) so position is visible
        start_angle_deg = -90
        end_angle_deg = start_angle_deg + 360 * fraction
        cv2.ellipse(
            frame,
            (self.x, self.y),
            (self.radius - 5, self.radius - 5),
            0,
            start_angle_deg,
            end_angle_deg,
            (150, 200, 255),
            1,
        )

        # Playhead line (from center to current angle)
        angle_rad = np.deg2rad(start_angle_deg + 360 * fraction)
        rx = (self.radius - 8) * np.cos(angle_rad)
        ry = (self.radius - 8) * np.sin(angle_rad)
        pt = (self.x + int(rx), self.y + int(ry))
        cv2.line(frame, (self.x, self.y), pt, (255, 255, 255), 2)

        # Small center dot
        cv2.circle(frame, (self.x, self.y), 3, (180, 180, 180), -1)
