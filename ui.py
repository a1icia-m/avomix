import cv2


class Button:
    def __init__(self, x, y, width, height, color=(0, 0, 0), active_color=(0, 255, 0)):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.color = color
        self.active_color = active_color
        self.pinched = {"Left": False, "Right": False}
        self.on = False

    def contains(self, pos):
        if pos is None:
            return False
        px, py = pos
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height

    def update(self, hand, pos):
        inside = self.contains(pos)
        if inside and not self.pinched[hand]:
            self.pinched[hand] = True
            self.on = not self.on
            if self.on:
                self.activate()
            else:
                self.deactivate()
            return True
        if not inside:
            self.pinched[hand] = False
        return False

    def draw(self, frame):
        color = self.active_color if self.on else self.color
        cv2.rectangle(
            frame,
            (self.x, self.y),
            (self.x + self.width, self.y + self.height),
            color,
            3,
        )

    def activate(self):
        pass

    def deactivate(self):
        pass


class PlayButton(Button):
    """Tap to play/pause left or right song."""

    def __init__(self, x, y, width, height, selector, side, **kwargs):
        super().__init__(x, y, width, height, **kwargs)
        self.selector = selector
        self.side = side

    def activate(self):
        self.selector.play(self.side)

    def deactivate(self):
        self.selector.pause(self.side)
