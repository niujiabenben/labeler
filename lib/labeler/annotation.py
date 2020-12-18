#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

class BoundingBox:
    def __init__(self, x1=-1, y1=-1, x2=-1, y2=-1):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

    def valid(self):
        return min(self.x1, self.y1, self.x2, self.y2) >= 0

    def increase(self, scale):
        self.x1 = int(round(self.x1 * scale))
        self.y1 = int(round(self.y1 * scale))
        self.x2 = int(round(self.x2 * scale))
        self.y2 = int(round(self.y2 * scale))

    def decrease(self, scale):
        self.increase(1.0 / scale)

    def contains(self, *, point=None, bbox=None):
        if point is not None:
            bbox = BoundingBox(*point, *point)
        if isinstance(bbox, (tuple, list)):
            bbox = BoundingBox(*bbox)
        a1, b1, a2, b2 = bbox.bbox
        x1, y1, x2, y2 = self.bbox
        return x1 <= a1 <= a2 <= x2 and y1 <= b1 <= b2 <= y2

    def intersect(self, other):
        sx1, sy1, sx2, sy2 = self.bbox
        ox1, oy1, ox2, oy2 = other.bbox
        x1 = max(sx1, ox1)
        y1 = max(sy1, oy1)
        x2 = min(sx2, ox2)
        y2 = min(sy2, oy2)
        if x1 <= x2 and y1 <= y2:
            return BoundingBox(x1, y1, x2, y2)
        return BoundingBox()

    def iou(self, other):
        intersect = self.intersect(other)
        return intersect.area / (self.area + other.area - intersect.area)

    @property
    def top_left(self):
        return min(self.x1, self.x2), min(self.y1, self.y2)

    @property
    def bottom_right(self):
        return max(self.x1, self.x2), max(self.y1, self.y2)

    @property
    def bbox(self):
        x1, y1 = self.top_left
        x2, y2 = self.bottom_right
        return x1, y1, x2, y2

    @property
    def width(self):
        return abs(self.x1 - self.x2) + 1

    @property
    def height(self):
        return abs(self.y1 - self.y2) + 1

    @property
    def area(self):
        return self.width * self.height

    @property
    def center(self):
        x1, y1 = self.top_left
        return x1 + self.width // 2, y1 + self.height // 2

    @property
    def aspect_ratio(self):
        return self.width / self.height

    def __str__(self):
        x1, y1, x2, y2 = self.bbox
        return f"bbox: [x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}]"


if __name__ == "__main__":
    pass
