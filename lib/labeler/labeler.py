#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

import os
import cv2
import copy
import logging

import lib.util


# 回调函数需要在全局空间中定义, 所以从Labeler中独立出来.
# 这里只是简单调用Labeler中的方法, 真正的实现还是在Labeler中.
def _on_mouse_callback(event, x, y, flags, self):
    self._mouse_callback(event, x, y, flags)


class Labeler:
    """标注类的基类. 其他标注类可以继承自本类.

    本类需要的参数由params传入, params为dict类型, 其中key的含义如下:
    img_dir:  图像文件目录
    ann_dir:  标注文件目录
    samples:  样本列表文件, 每一行代表一个样本. 不能有扩展名.
    snapshot: 标注进度文件

    本类定义了以下基本动作:
    [enter] or 'f':      前进一个样本
    [backspace] or 'b':  后退一个样本
    's':                 保存当前标注

    继承本类时, 需要注意:
    1. self.curr_annotations纪录当前样本的标注信息, 其初始值为: None
    """

    def __init__(self, params):
        self.img_dir = params["img_dir"]
        self.ann_dir = params["ann_dir"]
        self.snapshot_file = params["snapshot"]
        self.samples = lib.util.read_list_file(params["samples"])
        self.samples_id = self._load_snapshot()
        # 工作中的变量
        self.curr_image = None
        self.curr_annotations = None

    def _load_snapshot(self):
        if os.path.exists(self.snapshot_file):
            content = lib.util.read_json_file(self.snapshot_file)
            if 0 <= content["samples_id"] < len(self.samples):
                return content["samples_id"]
        return 0

    def _save_snapshot(self):
        lib.util.write_json_file({
            "samples_id": self.samples_id
        }, self.snapshot_file)

    def _load_image(self, samples_id):
        name = self.samples[samples_id] + ".jpg"
        path = os.path.join(self.img_dir, name)
        image = cv2.imread(path, 1)
        assert image is not None, f"Failed to load image: {path}"
        return image

    def _load_annotations(self, samples_id):
        name = self.samples[samples_id] + ".json"
        path = os.path.join(self.ann_dir, name)
        if not os.path.exists(path): return None
        return lib.util.read_json_file(path)

    def _load_curr_sample(self):
        self.curr_image = self._load_image(self.samples_id)
        self.curr_annotations = self._load_annotations(self.samples_id)

    def _save_annotations(self, annotations, samples_id):
        if not annotations: return
        name = self.samples[samples_id] + ".json"
        path = os.path.join(self.ann_dir, name)
        lib.util.write_json_file(annotations, path)

    def _save_curr_sample(self):
        self._save_annotations(self.curr_annotations, self.samples_id)
        self._save_snapshot()

    def _move(self, step):
        samples_id = self.samples_id + step
        if samples_id < 0:
            logging.info("We reach the beginning.")
        elif samples_id >= len(self.samples):
            logging.info("We reach the end.")
        else:
            self._save_curr_sample()
            self.samples_id = samples_id
            self._load_curr_sample()

    def _draw_text_lines(self, image):
        # 这里仅仅写上标注进度, 如需写其他信息可以重载这个函数
        origin, color = (20, 20), (0, 0, 255)
        line = f"Progress: {self.samples_id+1}/{len(self.samples)}"
        return lib.util.draw_textlines(image, origin, line, color)

    def _draw_curr_image(self):
        # 这里仅仅在图像中显示进度, 需要重载此函数来画标注信息
        self._draw_text_lines(copy.deepcopy(self.curr_image))

    # 如果需要鼠标响应事件, 请重载这个函数
    def _mouse_callback(self, event, x, y, flags):
        pass

    def _key_callback(self, key):
        if key == 255 or key == -1: return
        logging.info("Pressed key: %d", key)
        if key == ord("\r"):
            self._move(1)
        elif key == ord("\b"):
            self._move(-1)
        elif key == ord("f"):
            self._move(1)
        elif key == ord("b"):
            self._move(-1)
        elif key == ord("s"):
            self._save_curr_sample()

    def run(self):
        cv2.namedWindow("img")
        cv2.setMouseCallback("img", _on_mouse_callback, self)

        self._load_curr_sample()
        while True:
            display = self._draw_curr_image()
            cv2.imshow("img", display)
            key = cv2.waitKey(20)
            if key == 27:
                self._save_curr_sample()
                break
            self._key_callback(key)


class ScaleLabeler(Labeler):
    """支持缩放的标注类.

    因为scale会变化, 本类(及其继承类)所有的标注数据都相对于原始图像.
    显示时, 需要将所有的标注映射回显示图像然后再作绘画.

    本类在基类Labeler的基础上新增了一下动作:
    'a':                 返回到原始图像
    鼠标滚轮:             放大/缩小图像
    鼠标左键按下拖动:      选择roi区域
    """

    def __init__(self, params, scale=1.0):
        super().__init__(params=params)
        self.base_scale = scale
        self.curr_scale = scale
        self.curr_roi = None
        self.cache_roi = None

    def _map_to(self, point):
        offset_x, offset_y = self.curr_roi.top_left
        x = (point[0] - offset_x) * self.curr_scale
        y = (point[1] - offset_y) * self.curr_scale
        return int(round(x)), int(round(y))

    def _map_back(self, point):
        offset_x, offset_y = self.curr_roi.top_left
        x = point[0] / self.curr_scale + offset_x
        y = point[1] / self.curr_scale + offset_y
        return int(round(x)), int(round(y))

    def _load_curr_sample(self):
        super()._load_curr_sample()
        height, width = self.curr_image.shape[:2]
        self.curr_roi = lib.labeler.BoundingBox(0, 0, width, height)
        self.curr_scale = self.base_scale
        self.cache_roi = None

    def _draw_bounding_box(self, image, bbox, color, thickness):
        if bbox is None: return image
        if not bbox.valid(): return image
        pt1 = self._map_to(bbox.top_left)
        pt2 = self._map_to(bbox.bottom_right)
        cv2.rectangle(image, pt1, pt2, color, thickness=thickness)
        return image

    def _extract_image(self, image, roi):
        x1, y1, x2, y2 = roi.bbox
        image = image[y1:y2, x1:x2, :]
        height, width = image.shape[:2]
        new_height = int(round(height * self.curr_scale))
        new_width = int(round(width * self.curr_scale))
        image = cv2.resize(image, (new_width, new_height))
        return image

    def _draw_curr_image(self):
        show = self._extract_image(self.curr_image, self.curr_roi)
        show = self._draw_text_lines(show)
        show = self._draw_bounding_box(show, self.cache_roi, (0, 0, 255), 1)
        return show

    def _mouse_callback(self, event, x, y, flags):
        super()._mouse_callback(event, x, y, flags)
        x, y = self._map_back(point=(x, y))
        if event == cv2.EVENT_LBUTTONDOWN:
            self.cache_roi = lib.labeler.BoundingBox()
            self.cache_roi.x1 = x
            self.cache_roi.y1 = y
        elif event == cv2.EVENT_LBUTTONUP:
            if self.cache_roi is not None:
                self.cache_roi.x2 = x
                self.cache_roi.y2 = y
                if self.cache_roi.area > 2500:
                    scale_1 = self.curr_roi.width / self.cache_roi.width
                    scale_2 = self.curr_roi.height / self.cache_roi.height
                    self.curr_scale *= min(scale_1, scale_2)
                    self.curr_scale = max(self.curr_scale, 1.2)
                    self.curr_roi = self.cache_roi
            self.cache_roi = None
        elif event == cv2.EVENT_MOUSEMOVE:
            if flags == cv2.EVENT_FLAG_LBUTTON:
                if self.cache_roi is not None:
                    self.cache_roi.x2 = x
                    self.cache_roi.y2 = y
            else:
                self.cache_roi = None
        elif event == cv2.EVENT_MOUSEWHEEL:
            change = 0.02 if self.curr_scale < self.base_scale else 0.01
            scale = 1.0 - change if flags > 0 else 1.0 + change
            self.curr_scale *= scale

    def _key_callback(self, key):
        super()._key_callback(key)
        if key == ord("a"):
            self.curr_scale = self.base_scale
            height, width = self.curr_image.shape[:2]
            self.curr_roi = lib.labeler.BoundingBox(0, 0, width, height)
            self.cache_roi = None


if __name__ == "__main__":
    pass
