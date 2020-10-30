#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

class BoundingBox:
    def __init__(self):
        self.x1 = self.y1 = self.x2 = self.y2 = -1

    def reset(self):
        self.x1 = self.y1 = self.x2 = self.y2 = -1

    def valid(self):
        return min(self.x1, self.y1, self.x2, self.y2) >= 0

    def is_inside(self, x, y):
        x1, y1, x2, y2 = self.get_bbox()
        return self.valid() and x1 <= x <= x2 and y1 <= y <= y2

    def top_left(self):
        return min(self.x1, self.x2), min(self.y1, self.y2)

    def bottom_right(self):
        return max(self.x1, self.x2), max(self.y1, self.y2)

    def get_bbox(self):
        x1, y1 = self.top_left()
        x2, y2 = self.bottom_right()
        return x1, y1, x2, y2

    def get_size(self):
        x1, y1, x2, y2 = self.get_bbox()
        return x2 - x1, y2 - y1

    def get_area(self):
        width, height = self.get_size()
        return width * height

    def __str__(self):
        x1, y1, x2, y2 = self.get_bbox()
        return f"bbox: [{x1}, {y1}, {x2}, {y2}]"


if __name__ == "__main__":
    pass
