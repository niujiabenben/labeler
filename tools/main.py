#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

# pylint: disable=unused-import
# pylint: disable=wrong-import-order

import logging

import init
import lib.util


def main():
    logging.info("log in color: %s", lib.util.BLACK("black"))
    logging.info("log in color: %s", lib.util.RED("Red"))
    logging.info("log in color: %s", lib.util.GREEN("Green"))
    logging.info("log in color: %s", lib.util.YELLOW("yellow"))
    logging.info("log in color: %s", lib.util.BLUE("Blue"))
    logging.info("log in color: %s", lib.util.MAGENTA("magenta"))
    logging.info("log in color: %s", lib.util.CYAN("cyan"))
    logging.info("log in color: %s", lib.util.WHITE("white"))
    logging.info("log in color: %s", lib.util.GRAY("gray"))


if __name__ == '__main__':
    lib.util.initialize_logger()
    main()
