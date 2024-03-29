#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

import math


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

    def translate(self, offset_x, offset_y):
        self.x1 += offset_x
        self.x2 += offset_x
        self.y1 += offset_y
        self.y2 += offset_y

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


class Line:
    """直线类, 方程为: ax + by + c = 0."""

    def __init__(self, a=0.0, b=0.0, c=0.0):
        self.epsilon = 1.0e-9
        self.a, self.b, self.c = a, b, c
        self._normalize()

    def _normalize(self):
        factor = max(abs(self.a), abs(self.b), abs(self.c), self.epsilon)
        self.a = float(self.a / factor)
        self.b = float(self.b / factor)
        self.c = float(self.c / factor)

    @staticmethod
    def create_from_points(x1, y1, x2, y2):  # 两点式
        return Line(y2 - y1, x1 - x2, x2 * y1 - y2 * x1)

    @staticmethod
    def create_from_pointk(x0, y0, a, b):  # 点斜式, 方向向量表示
        return Line(b, -a, a * y0 - b * x0)

    @staticmethod
    def create_from_pointa(x0, y0, angle):  # 点斜式, 方向角表示
        a, b = math.cos(angle), math.sin(angle)
        return Line.create_from_pointk(x0, y0, a, b)

    def get_x(self, y):
        return -(self.b * y + self.c) / self.a

    def get_y(self, x):
        return -(self.a * x + self.c) / self.b

    def get_cross_point(self, other):
        a1, b1, c1 = self.a, self.b, self.c
        a2, b2, c2 = other.a, other.b, other.c
        x = (c2 * b1 - c1 * b2) / (a1 * b2 - a2 * b1)
        y = (c2 * a1 - c1 * a2) / (a2 * b1 - a1 * b2)
        return x, y

    def move_to_point(self, x, y):
        self.c = -(self.a * x + self.b * y)
        self._normalize()
        return self

    def move_to_point_copy(self, x, y):
        return Line(self.a, self.a, -(self.a * x + self.b * y))

    def to_list(self):
        return [self.a, self.b, self.c]

    def parallel_to(self, other):
        return self.get_angle_with_line(other) < self.epsilon

    def parallel_to_axis_x(self):
        return self.parallel_to(Line.create_from_points(0, 0, 1, 0))

    def parallel_to_axis_y(self):
        return self.parallel_to(Line.create_from_points(0, 0, 0, 1))

    def get_angle_with_line(self, other):
        """返回两直线夹角, 范围为: [0, pi/2]"""

        numerator = self.a * other.a + self.b * other.b
        self_norm = self.a * self.a + self.b * self.b
        other_norm = other.a * other.a + other.b * other.b
        denominator = math.sqrt(self_norm * other_norm)
        cos_theta = math.fabs(numerator / denominator)
        # 某些情况下, 由于有计算误差, 所以cos_theta的值可能比1大一点点
        cos_theta = min(cos_theta, 1.0)
        return math.acos(cos_theta)

    def get_slant_angle(self):
        """返回倾斜角, 范围为: [0, pi]"""

        axis_x = Line.create_from_points(0, 0, 1, 0)
        angle = self.get_angle_with_line(axis_x)
        if self.a * self.b > 0: angle = math.pi - angle
        return angle

    def get_distance(self, x=0, y=0):
        numerator = self.a * x + self.b * y + self.c
        denominator = math.sqrt(self.a ** 2 + self.b ** 2)
        return math.fabs(numerator) / denominator

    # 线在点的左边
    def left_to(self, x, y):
        if self.parallel_to_axis_x(): return False
        return self.get_x(y) < x

    # 线在点的右边
    def right_to(self, x, y):
        if self.parallel_to_axis_x(): return False
        return self.get_x(y) > x

    # 线在点的上边, 注意这里坐标系和图像坐标系不同
    def above_to(self, x, y):
        if self.parallel_to_axis_y(): return False
        return self.get_y(x) > y

    # 线在点的下边, 注意这里坐标系和图像坐标系不同
    def below_to(self, x, y):
        if self.parallel_to_axis_y(): return False
        return self.get_y(x) < y


if __name__ == "__main__":
    pass
