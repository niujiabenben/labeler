#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

"""点标注的示例程序.

数据的layout请参考: lib.labeler.Labeler.

左键单击选点, 左键按下拖动选择区域, 右键单击删除区域中的点.
"""

import os
import cv2
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

    def _load_curr_image(self):
        image = super()._load_curr_image()
        height, width = image.shape[:2]
        self.curr_roi

    def _draw_curr_image(self):
        x1, y1, x2, y2 = self.curr_roi
        show = self.curr_image[y1:y2, x1:x2, :]

        width, height = x2 - x1
        cv2.resize()

        text = f"Progress: {self.samples_id + 1}/{len(self.samples)}"
        show = lib.util.draw_textlines(show, (20, 20), text, (0, 0, 255))

        for bbox in self.curr_annotations:
            pt1, pt2 = bbox.top_left, bbox.bottom_right
            cv2.rectangle(show, pt1, pt2, (0, 0, 255), thickness=1)
        if self.selected_region:
            pt1 = self.selected_region.top_left
            pt2 = self.selected_region.bottom_right
            cv2.rectangle(show, pt1, pt2, (0, 0, 255), thickness=2)
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
                if self.cache_data.area > 400:
                    self.curr_annotations.append(self.cache_data)
                self.cache_data = None
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.cache_data is None:
                self.selected_region = self._select_region(x, y)
            else:
                self.cache_data.x2 = x
                self.cache_data.y2 = y
            self.cursor = (x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._delete_selected_region()

    def _key_callback(self, key):
        if key != 255 and key != -1:
            logging.info("Pressed key: %d", key)
        super()._key_callback(key)
        if key == ord("d"):  # 按d删除选中的区域
            self._delete_selected_region()


if __name__ == "__main__":
    lib.util.initialize_logger()
    RegionLabeler("../data", scale=0.55).run()
    print("Done!")
