#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

import cv2
import copy
import logging

import init
import lib.util
import lib.labeler


class PointLabeler(lib.labeler.Labeler):
    def __init__(self, root_dir, scale=1.0):
        super().__init__(root_dir)
        self.scale = scale

    def _load_curr_image(self):
        image = super()._load_curr_image()
        height, width = image.shape[:2]
        height = int(round(height * self.scale))
        width = int(round(width * self.scale))
        return cv2.resize(image, (width, height))

    def _load_curr_annotations(self):
        annotations = []
        for x, y in super()._load_curr_annotations():
            x = int(round(x * self.scale))
            y = int(round(y * self.scale))
            annotations.append((x, y))
        return annotations

    def _save_curr_annotations(self):
        annotations = []
        for x, y in self.curr_annotations:
            x = int(round(x / self.scale))
            y = int(round(y / self.scale))
            annotations.append((x, y))
        self.curr_annotations = annotations
        super()._save_curr_annotations()

    def _find_selected_points(self):
        bbox = self.cache_data or lib.labeler.BoundingBox()
        return [pt for pt in self.curr_annotations if bbox.is_inside(*pt)]

    def _draw_curr_image(self):
        show = super()._draw_curr_image()
        for x, y in self.curr_annotations:
            cv2.circle(show, (x, y), 4, (0, 255, 255), thickness=-1)
        for x, y in self._find_selected_points():
            cv2.circle(show, (x, y), 8, (0, 0, 255), thickness=-1)
        if self.cache_data and self.cache_data.valid():
            pt1 = (self.cache_data.x1, self.cache_data.y1)
            pt2 = (self.cache_data.x2, self.cache_data.y2)
            cv2.rectangle(show, pt1, pt2, (0, 0, 255), thickness=2)
        return show

    def _mouse_callback(self, event, x, y, flags):
        # 左键按下, 选择一个点
        if event == cv2.EVENT_LBUTTONDOWN:
            self.cache_data = lib.labeler.BoundingBox()
            self.cache_data.x1 = x
            self.cache_data.y1 = y
        # 左键抬起, 选择另一个点, 如果这个点和前一个点相同, 则为单击.
        # 如果两个点不同, 则为拖动. 单击选点, 拖动选区域.
        elif event == cv2.EVENT_LBUTTONUP:
            self.cache_data.x2 = x
            self.cache_data.y2 = y
            if self.cache_data.x1 == x and self.cache_data.y1 == y:
                self.curr_annotations.append((x, y))
                self.cache_data = None
            elif self.cache_data.get_area() < 400:
                self.cache_data = None
        elif event == cv2.EVENT_MOUSEMOVE:
            # 这个flag表示鼠标拖动时左键为按下状态
            if flags == cv2.EVENT_FLAG_LBUTTON:
                self.cache_data.x2 = x
                self.cache_data.y2 = y
        # 右键单击删除选中的点
        elif event == cv2.EVENT_RBUTTONDOWN:
            for pt in self._find_selected_points():
                self.curr_annotations.remove(pt)
            self.cache_data = None

    def _key_callback(self, key):
        if key != 255 and key != -1:
            logging.info("Pressed key: %d", key)
        super()._key_callback(key)
        if key == ord("d"):  # 按d删除选中的点
            for pt in self._find_selected_points():
                self.curr_annotations.remove(pt)
            self.cache_data = None


if __name__ == "__main__":
    lib.util.initialize_logger()
    PointLabeler("../data", scale=0.75).run()
    print("Done!")
