#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

# pylint: disable=unused-import
# pylint: disable=wrong-import-order

import unittest

import init
import lib.util


class TestMultiTask(unittest.TestCase):

    def test_function_args_none(self):
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=1,
                taskfun=lambda: 1,
                samples=[tuple()] * 10,
            ), [1] * 10)
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=4,
                taskfun=lambda: 1,
                samples=[tuple()] * 10,
            ), [1] * 10)

    def test_function_args_one(self):
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=1,
                taskfun=lambda x: x + 1,
                samples=list(range(10)),
            ), list(range(1, 11)))  # yapf: disable
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=4,
                taskfun=lambda x: x + 1,
                samples=list(range(10)),
            ), list(range(1, 11)))  # yapf: disable

    def test_function_args_two(self):
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=1,
                taskfun=(lambda x, y: x + y),
                samples=[(x, -x) for x in range(10)],
            ), [0] * 10)
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=4,
                taskfun=(lambda x, y: x + y),
                samples=[(x, -x) for x in range(10)],
            ), [0] * 10)

    def test_function_args_common_one(self):
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=1,
                taskfun=lambda x: x + 1,
                samples=[tuple()] * 10,
                args=4,
            ), [5] * 10)
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=4,
                taskfun=lambda x: x + 1,
                samples=[tuple()] * 10,
                args=4,
            ), [5] * 10)

    def test_function_args_common_tuple(self):
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=1,
                taskfun=lambda x,
                y: x + y,
                samples=[tuple()] * 10,
                args=(4, 5),
            ), [9] * 10)
        self.assertEqual(
            lib.util.TaskPool.map(
                numthreads=4,
                taskfun=lambda x,
                y: x + y,
                samples=[tuple()] * 10,
                args=(4, 5),
            ), [9] * 10)

    def test_class_args_none(self):

        class TestClass:

            def __init__(self):
                self.value = 1

            def process(self):
                return self.value + 1

        pool = lib.util.TaskPool(TestClass, [tuple()])
        result = pool.process([tuple()] * 10)
        self.assertEqual(result, [2] * 10)
        pool.finish()

        pool = lib.util.TaskPool(TestClass, [tuple()] * 4)
        result = pool.process([tuple()] * 10)
        self.assertEqual(result, [2] * 10)
        pool.finish()

    def test_class_args_one(self):

        class TestClass:

            def __init__(self, value):
                self.value = value

            def process(self, num):
                return self.value + num

        pool = lib.util.TaskPool(TestClass, [1])
        result = pool.process(list(range(10)))
        self.assertEqual(result, list(range(1, 11)))
        pool.finish()

        pool = lib.util.TaskPool(TestClass, [1] * 4)
        result = pool.process(list(range(10)))
        self.assertEqual(result, list(range(1, 11)))
        pool.finish()

    def test_class_args_two(self):

        class TestClass:

            def __init__(self, x, y):
                self.x = x
                self.y = y

            def process(self, a, b):
                return self.x + self.y + a + b

        pool = lib.util.TaskPool(TestClass, [(1, -1)])
        result = pool.process([(x, -x) for x in range(10)])
        self.assertEqual(result, [0] * 10)
        pool.finish()

        pool = lib.util.TaskPool(TestClass, [(1, -1)] * 4)
        result = pool.process([(x, -x) for x in range(10)])
        self.assertEqual(result, [0] * 10)
        pool.finish()


if __name__ == '__main__':
    unittest.main()
