#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

"""点标注的示例程序.

数据的layout请参考: lib.labeler.Labeler.

左键单击选点, 左键按下拖动选择区域, 右键单击删除区域中的点.
"""

import os
import cv2
import copy
import logging

import init
import lib.util
import lib.labeler


class RegionLabeler(lib.labeler.ScaleLabeler):
    def __init__(self, params, scale=1.0):
        super().__init__(params, scale)
        self.selected_region = None
        self.cache_region = None
        self.cursor = None

    def _load_annotations(self, samples_id):
        annotations = super()._load_annotations(samples_id) or []
        return [lib.labeler.BoundingBox(*ann) for ann in annotations]

    def _load_curr_sample(self):
        super()._load_curr_sample()
        self.selected_region = None
        self.cache_region = None
        self.cursor = None

    def _save_annotations(self, annotations, samples_id):
        if not annotations: return
        annotations = [ann.bbox for ann in annotations]
        super()._save_annotations(annotations, samples_id)

    def _draw_curr_image(self):
        show = super()._draw_curr_image()
        # draw rectangles (bbox相对于原始图像)
        for bbox in self.curr_annotations:
            thickness = 2 if bbox is self.selected_region else 1
            self._draw_bounding_box(show, bbox, (0, 0, 255), thickness)
        if self.cache_region and self.cache_region.valid():
            self._draw_bounding_box(show, self.cache_region, (0, 0, 255), 1)
        # cursor相对于显示窗口
        if (not self.cache_region) and self.cursor:
            x, y = self.cursor
            height, width = show.shape[:2]
            cv2.line(show, (x, y), (width, y), (0, 0, 255), 1)
            cv2.line(show, (x, y), (x, height), (0, 0, 255), 1)
        return show

    def _select_region(self, x, y):
        def check_fun(bbox): return bbox.contains(point=(x, y))
        selected = list(filter(check_fun, self.curr_annotations))
        if not selected: return None
        return max(selected, key=lambda bbox: bbox.area)

    def _delete_selected_region(self):
        if self.selected_region:
            self.curr_annotations.remove(self.selected_region)
        self.selected_region = None
        self.cache_region = None
        self.cursor = None

    def _mouse_callback(self, event, x, y, flags):
        super()._mouse_callback(event, x, y, flags)
        ox, oy = self._map_back(point=(x, y))
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.cache_region is None:
                self.cache_region = lib.labeler.BoundingBox()
                self.cache_region.x1 = ox
                self.cache_region.y1 = oy
            else:
                self.cache_region.x2 = ox
                self.cache_region.y2 = oy
                if self.cache_region.area > 400:
                    self.curr_annotations.append(self.cache_region)
                self.cache_region = None
        elif event == cv2.EVENT_MOUSEMOVE:
            self.cursor = None
            if flags == cv2.EVENT_FLAG_LBUTTON:
                self.cache_region = None
            elif self.cache_region:
                self.cache_region.x2 = ox
                self.cache_region.y2 = oy
            else:
                self.selected_region = self._select_region(ox, oy)
                self.cursor = (x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._delete_selected_region()

    def _key_callback(self, key):
        super()._key_callback(key)
        if key == ord("d"):  # 按d删除选中的区域
            self._delete_selected_region()
        elif key == ord("c"):
            self.curr_annotations = []


if __name__ == "__main__":
    lib.util.initialize_logger()
    RegionLabeler({
        "img_dir": "../data/images",
        "ann_dir": "../data/annotations",
        "snapshot": "../data/snapshot.json",
        "samples": "../data/samples.txt"
    }, scale=0.55).run()
    print("Done!")
