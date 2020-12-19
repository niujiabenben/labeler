#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

"""点标注的示例程序.

数据的layout请参考: lib.labeler.Labeler.

左键按下添加标注点, 鼠标拖动选择与鼠标最近的标注点, 右键单击删除选中的标注点.
"""

import cv2
import logging

import init
import lib.util
import lib.labeler


class PointLabeler(lib.labeler.Labeler):
    def __init__(self, root_dir, scale=1.0):
        super().__init__(root_dir)
        self.scale = scale
        self.selected_point = None

    def _load_image(self, samples_id):
        image = super()._load_image(samples_id)
        height, width = image.shape[:2]
        height = int(round(height * self.scale))
        width = int(round(width * self.scale))
        return cv2.resize(image, (width, height))

    def _load_annotations(self, samples_id):
        annotations = []
        content = super()._load_annotations(samples_id)
        if not content: return annotations
        for x, y in content:
            x = int(round(x * self.scale))
            y = int(round(y * self.scale))
            annotations.append((x, y))
        return annotations

    def _save_annotations(self, annotations):
        to_be_saved = []
        for x, y in self.curr_annotations:
            x = int(round(x / self.scale))
            y = int(round(y / self.scale))
            to_be_saved.append((x, y))
        super()._save_annotations(to_be_saved)

    def _draw_curr_image(self):
        show = super()._draw_curr_image()
        for x, y in self.curr_annotations:
            cv2.circle(show, (x, y), 4, (0, 255, 255), thickness=-1)
        if self.selected_point:
            cv2.circle(show, self.selected_point, 8, (0, 0, 255), thickness=-1)
        return show

    def _get_closest_point(self, x, y):
        if not self.curr_annotations: return None, None
        distances = []
        for x1, y1 in self.curr_annotations:
            dist = (x1 - x) ** 2 + (y1 - y) ** 2
            distances.append(((x1, y1), dist))
        return min(distances, key=lambda v: v[-1])

    def _mouse_callback(self, event, x, y, flags):
        # 左键按下, 添加一个标注点
        if event == cv2.EVENT_LBUTTONDOWN:
            point, dist = self._get_closest_point(x, y)
            if point is None or dist > 1600:
                self.curr_annotations.append((x, y))
        # 鼠标拖动, 选择一个标注点
        elif event == cv2.EVENT_MOUSEMOVE:
            self.selected_point = None
            point, dist = self._get_closest_point(x, y)
            if point is not None and dist < 1600:
                self.selected_point = point
        # 右键单击删除选中的标注点
        elif event == cv2.EVENT_RBUTTONDOWN:
            if self.selected_point:
                self.curr_annotations.remove(self.selected_point)
                self.selected_point = None

    def _key_callback(self, key):
        if key != 255 and key != -1:
            logging.info("Pressed key: %d", key)
        super()._key_callback(key)
        if key == ord("d"):
            if self.selected_point:
                self.curr_annotations.remove(self.selected_point)
                self.selected_point = None
        elif key == ord("c"):
            self.curr_annotations = []


if __name__ == "__main__":
    lib.util.initialize_logger()
    PointLabeler("../data", scale=0.55).run()
    print("Done!")
