#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

import os
import json
import pickle
import logging
import datetime
import multiprocessing

global_lock = multiprocessing.Lock()


def prepare_dir(path):
    """Make dir if necessary."""

    dirname = os.path.dirname(path)
    # 当前目录直接返回
    if not dirname: return None

    with global_lock:
        os.makedirs(dirname, exist_ok=True)


def read_pickle_file(path):
    "Read file in pickle format."

    if not path: return None
    with open(path, "rb") as srcfile:
        return pickle.load(srcfile)


def read_json_file(path):
    "Read file in json format."

    if not path: return None
    with open(path, "rb") as srcfile:
        return json.load(srcfile)


def read_list_file(path, sep=None):
    "Read file as a list of strings."

    if not path: return None
    with open(path, "r") as srcfile:
        if isinstance(sep, str):
            return [l.strip().split(sep) for l in srcfile]
        return [l.strip() for l in srcfile]


def read_list_field(path, field=0, sep=" "):
    "Read file and extract filed."

    lines = read_list_file(path, sep)
    if not lines: return None
    if isinstance(field, int):
        return [n[field] for n in lines]
    return [[n[i] for i in field] for n in lines]


def read_map_file(path):
    "Read file as a dictionay."

    if not path: return None
    with open(path, "r") as srcfile:
        lines = [l.strip().split() for l in srcfile]
    return dict(lines)


def write_pickle_file(data, path):
    """Write data to pickle file."""

    prepare_dir(path)
    with open(path, "wb") as dstfile:
        pickle.dump(data, dstfile, protocol=2)


def write_json_file(data, path):
    """Write data to json file."""

    prepare_dir(path)
    with open(path, "w") as dstfile:
        json.dump(data, dstfile, indent=2)


def write_list_file(data, path, sep=" "):
    """Write list to txt file."""

    prepare_dir(path)
    with open(path, "w") as dstfile:
        for line in data:
            if isinstance(line, (tuple, list)):
                line = sep.join([str(item) for item in line])
            dstfile.write(line + "\n")


def initialize_logger(name=None, file=None, display=True):
    """Configurate logger based on settings.

    Args:
        name: str. Logger name, 'None' means root logger.
        file: str. Path of file to log to, 'None' or empty string to disable
            logging to file.
        display: bool. Indicate whether the logger logs to console or not.

    Returns:
        The required logger instance.
    """

    logger = logging.getLogger(name)
    if logger.handlers: return logger

    # 局部的logger是全局logger的child, 这里防止局部的log扩散到全局log中
    logger.propagate = False
    logger.setLevel(logging.INFO)

    fmt = "%(asctime)s %(filename)s:%(lineno)d] %(levelname)s: %(message)s"
    fmt = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    if file:
        prepare_dir(file)
        handler = logging.FileHandler(file)
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    if display:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)

    return logger


def get_global_logger(logging_root):
    date = str(datetime.date.today())
    logging_file = os.path.join(logging_root, date, "log_global.txt")
    prepare_dir(logging_file)
    return initialize_logger(None, logging_file, True)


def get_local_logger(name, logging_root):
    assert name != "global"
    date = str(datetime.date.today())
    logging_file = os.path.join(logging_root, date, f"log_{name}.txt")
    prepare_dir(logging_file)
    return initialize_logger(name, logging_file, False)


def COLOR(text, color):
    # yapf: disable
    ansi_colors = {
        "black":     "0;30",    "bright black":     "0;90",
        "red":       "0;31",    "bright red":       "0;91",
        "green":     "0;32",    "bright green":     "0;92",
        "yellow":    "0;33",    "bright yellow":    "0;93",
        "blue":      "0;34",    "bright blue":      "0;94",
        "magenta":   "0;35",    "birght magenta":   "0;95",
        "cyan":      "0;36",    "bright cyan":      "0;96",
        "white":     "0;37",    "brignt white":     "0;97",
    }
    # yapf: enable
    all_colors = {}
    for key, value in ansi_colors.items():
        all_colors[key.lower().replace(" ", "")] = value
    all_colors["gray"] = ansi_colors["bright black"]

    color = color.lower().replace(" ", "")
    assert color in all_colors, f"Unknown color: {color}"
    return f"\033[{all_colors[color]}m{text}\033[0m"


# yapf: disable
def BLACK(text):    return COLOR(text, "black")
def RED(text):      return COLOR(text, "red")
def GREEN(text):    return COLOR(text, "green")
def YELLOW(text):   return COLOR(text, "yellow")
def BLUE(text):     return COLOR(text, "blue")
def MAGENTA(text):  return COLOR(text, "magenta")
def CYAN(text):     return COLOR(text, "cyan")
def WHITE(text):    return COLOR(text, "white")
def GRAY(text):     return COLOR(text, "gray")


if __name__ == "__main__":
    pass
