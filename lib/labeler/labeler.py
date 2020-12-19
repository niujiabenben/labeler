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

    为了简单起见, 假设所有的数据都放在root_dir中, 具体如下:
    ${root_dir}/images:        图像文件目录
    ${root_dir}/annotations:   标注文件目录
    ${root_dir}/samples.txt:   样本列表文件, 每一行代表一个样本. 不能有扩展名.
    ${root_dir}/snapshot.json: 标注进度文件

    继承本类时, 需要注意:
    1. self.curr_annotations纪录当前样本的标注信息, 其初始值为: None
    2. self.cache_data纪录标注过程中的中间信息, 其初始值为: None.
       每次切换样本的时候, 这个变量的值也会被重置.
    """

    def __init__(self, root_dir):
        self.img_dir = os.path.join(root_dir, "images")
        self.ann_dir = os.path.join(root_dir, "annotations")
        self.snapshot_file = os.path.join(root_dir, "snapshot.json")
        sample_file = os.path.join(root_dir, "samples.txt")
        self.samples = lib.util.read_list_file(sample_file)
        self.samples_id = self._load_snapshot()
        # 工作中的变量
        self.curr_image = None
        self.curr_annotations = None
        self.cache_data = None

    def _load_snapshot(self):
        if os.path.exists(self.snapshot_file):
            content = lib.util.read_json_file(self.snapshot_file)
            if 0 <= content["samples_id"] < len(self.samples):
                return content["samples_id"]
        return 0

    def _save_snapshot(self):
        lib.util.dump_to_json({
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
        self.cache_data = None

    def _save_annotations(self, annotations):
        if not annotations: return
        name = self.samples[self.samples_id] + ".json"
        path = os.path.join(self.ann_dir, name)
        lib.util.dump_to_json(annotations, path)

    def _save_curr_sample(self):
        self._save_annotations(self.curr_annotations)
        self._save_snapshot()
        self.cache_data = None

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

    def _draw_curr_image(self):
        # 这里仅仅在图像中显示进度, 需要重载此函数来画标注信息
        return lib.util.draw_textlines(
            image=copy.deepcopy(self.curr_image),
            origin=(20, 20),
            textlines=[f"Progress: {self.samples_id+1}/{len(self.samples)}"],
            color=(255, 255, 255))

    # 如果需要鼠标响应事件, 请重载这个函数
    def _mouse_callback(self, event, x, y, flags):
        pass

    def _key_callback(self, key):
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


if __name__ == "__main__":
    pass
