#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

"""点标注的示例程序.

数据的layout请参考: lib.labeler.Labeler.

左键单击添加标注点, 鼠标拖动选择与鼠标最近的标注点, 右键单击删除选中的标注点.
"""

import cv2
import logging

import init
import lib.util
import lib.labeler


class PointLabeler(lib.labeler.ScaleLabeler):
    def __init__(self, params, scale=1.0):
        super().__init__(params, scale)
        self.cache_point = None
        self.selected_point = None

    def _load_annotations(self, samples_id):
        return super()._load_annotations(samples_id) or []

    def _load_curr_sample(self):
        super()._load_curr_sample()
        self.cache_point = None
        self.selected_point = None

    def _draw_curr_image(self):
        show = super()._draw_curr_image()
        for x, y in self.curr_annotations:
            x, y = self._map_to(point=(x, y))
            cv2.circle(show, (x, y), 4, (0, 255, 255), thickness=-1)
        if self.selected_point:
            x, y = self._map_to(self.selected_point)
            cv2.circle(show, (x, y), 8, (0, 0, 255), thickness=-1)
        return show

    def _get_closest_point(self, x, y):
        distances = []
        for x1, y1 in self.curr_annotations:
            dist = (x1 - x) ** 2 + (y1 - y) ** 2
            distances.append(((x1, y1), dist))
        if not distances: return None, None
        return min(distances, key=lambda v: v[-1])

    def _mouse_callback(self, event, x, y, flags):
        super()._mouse_callback(event, x, y, flags)
        x, y = self._map_back(point=(x, y))
        # 鼠标左键按下, 纪录一个点
        if event == cv2.EVENT_LBUTTONDOWN:
            self.cache_point = lib.labeler.BoundingBox()
            self.cache_point.x1 = x
            self.cache_point.y1 = y
        # 鼠标左键抬起, 判断是否是单击
        elif event == cv2.EVENT_LBUTTONUP:
            if ((self.cache_point is not None) and
                    (self.cache_point.x1 == x) and
                    (self.cache_point.y1 == y)):
                point, dist = self._get_closest_point(x, y)
                if point is None or dist > 1600:
                    self.curr_annotations.append((x, y))
            self.cache_point = None
        # 鼠标拖动, 选择一个标注点
        elif event == cv2.EVENT_MOUSEMOVE:
            self.cache_point = None
            self.selected_point = None
            point, dist = self._get_closest_point(x, y)
            if point is not None and dist < 1600:
                self.selected_point = point
        # 鼠标右键按下, 删除选中的标注点
        elif event == cv2.EVENT_RBUTTONDOWN:
            if self.selected_point:
                self.curr_annotations.remove(self.selected_point)
                self.selected_point = None
                self.cache_point = None

    def _key_callback(self, key):
        super()._key_callback(key)
        if key == ord("d"):
            if self.selected_point:
                self.curr_annotations.remove(self.selected_point)
                self.selected_point = None
                self.cache_point = None
        elif key == ord("c"):
            self.curr_annotations = []


if __name__ == "__main__":
    lib.util.initialize_logger()
    PointLabeler({
        "img_dir": "../data/images",
        "ann_dir": "../data/annotations",
        "snapshot": "../data/snapshot.json",
        "samples": "../data/samples.txt"
    }, scale=0.55).run()
    print("Done!")
