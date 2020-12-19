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


class RegionLabeler(lib.labeler.Labeler):
    def __init__(self, root_dir, scale=1.0):
        super().__init__(root_dir)
        self.base_scale = scale
        self.curr_scale = scale
        self.curr_roi = None
        self.selected_region = None
        self.cursor = None

    def _load_annotations(self, samples_id):
        annotations = super()._load_annotations(samples_id)
        if annotations is None: return []
        return [lib.labeler.BoundingBox(*ann) for ann in annotations]

    def _load_curr_sample(self):
        super()._load_curr_sample()
        height, width = self.curr_image.shape[:2]
        self.curr_scale = self.base_scale
        self.curr_roi = lib.labeler.BoundingBox(0, 0, width, height)
        self.selected_region = None
        self.cursor = None

    def _save_annotations(self, annotations):
        if not annotations: return
        annotations = [ann.bbox for ann in annotations]
        super()._save_annotations(annotations)

    def _draw_rectangle(self, image, bbox, color, thickness=1):
        if not self.curr_roi.contains(bbox=bbox): return
        offset_x, offset_y = self.curr_roi.top_left
        bbox = copy.deepcopy(bbox)
        bbox.translate(-offset_x, -offset_y)
        bbox.increase(self.curr_scale)
        pt1, pt2 = bbox.top_left, bbox.bottom_right
        cv2.rectangle(image, pt1, pt2, color, thickness)

    def _draw_curr_image(self):
        # extract patch & resize
        x1, y1, x2, y2 = self.curr_roi.bbox
        show = self.curr_image[y1:y2, x1:x2, :]
        height, width = show.shape[:2]
        new_height = int(round(height * self.curr_scale))
        new_width = int(round(width * self.curr_scale))
        show = cv2.resize(show, (new_width, new_height))
        # draw progress
        text = f"Progress: {self.samples_id + 1}/{len(self.samples)}"
        show = lib.util.draw_textlines(show, (20, 20), text, (0, 0, 255))
        # draw rectangles (bbox相对于原始图像)
        for bbox in self.curr_annotations:
            self._draw_rectangle(show, bbox, (0, 0, 255))
        if self.selected_region:
            self._draw_rectangle(show, self.selected_region, (0, 0, 255), 2)
        # draw rectangles (bbox相对于显示窗口)
        if self.cache_data and self.cache_data.valid():
            pt1 = self.cache_data.top_left
            pt2 = self.cache_data.bottom_right
            cv2.rectangle(show, pt1, pt2, (0, 0, 255), thickness=1)
        if (not self.cache_data) and self.cursor:
            x, y = self.cursor
            height, width = show.shape[:2]
            cv2.line(show, (x, y), (width, y), (0, 0, 255), 1)
            cv2.line(show, (x, y), (x, height), (0, 0, 255), 1)
        return show

    def _select_region(self, x, y):
        if not self.curr_annotations: return None
        offset_x, offset_y = self.curr_roi.top_left
        x = int(round(x / self.curr_scale)) + offset_x
        y = int(round(y / self.curr_scale)) + offset_y
        selected = [bbox for bbox in self.curr_annotations
                    if bbox.contains(point=(x, y))]
        if not selected: return None
        return max(selected, key=lambda bbox: bbox.area)

    def _delete_selected_region(self):
        if self.selected_region:
            self.curr_annotations.remove(self.selected_region)
        self.selected_region = None
        self.cache_data = None
        self.cursor = None

    def _mouse_callback(self, event, x, y, flags):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.cache_data is None:
                self.cache_data = lib.labeler.BoundingBox()
                self.cache_data.x1 = x
                self.cache_data.y1 = y
            else:
                self.cache_data.x2 = x
                self.cache_data.y2 = y
                self.cache_data.decrease(self.curr_scale)
                self.cache_data.translate(*self.curr_roi.top_left)
                if self.cache_data.area > 400:
                    self.curr_annotations.append(self.cache_data)
                self.cache_data = None
        elif event == cv2.EVENT_LBUTTONUP:
            if ((self.cache_data is not None) and
                    (self.cache_data.x1 != x) and
                    (self.cache_data.y1 != y)):
                self.cache_data.x2 = x
                self.cache_data.y2 = y
                self.cache_data.decrease(self.curr_scale)
                self.cache_data.translate(*self.curr_roi.top_left)
                if self.cache_data.area > 2500:
                    scale_1 = self.curr_roi.width / self.cache_data.width
                    scale_2 = self.curr_roi.height / self.cache_data.height
                    self.curr_scale *= min(scale_1, scale_2)
                    self.curr_roi = self.cache_data
                self.cache_data = None
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.cache_data is None:
                self.selected_region = self._select_region(x, y)
            else:
                self.cache_data.x2 = x
                self.cache_data.y2 = y
            self.cursor = (x, y)
        # 右键删除选中区域
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._delete_selected_region()
        # 鼠标滚轮缩放图像
        elif event == cv2.EVENT_MOUSEWHEEL:
            scale = 0.99 if flags > 0 else 1.01
            self.curr_scale *= scale

    def _key_callback(self, key):
        if key != 255 and key != -1:
            logging.info("Pressed key: %d", key)
        super()._key_callback(key)
        if key == ord("d"):  # 按d删除选中的区域
            self._delete_selected_region()
        elif key == ord("a"):
            self.curr_scale = self.base_scale
            height, width = self.curr_image.shape[:2]
            self.curr_roi = lib.labeler.BoundingBox(0, 0, width, height)


if __name__ == "__main__":
    lib.util.initialize_logger()
    RegionLabeler("../data", scale=0.55).run()
    print("Done!")
