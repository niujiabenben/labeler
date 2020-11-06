#! /home/chenli/Documents/tools/anaconda3/envs/pytorch/bin/python
# coding: utf-8

import time
import dill
import logging
import multiprocessing


class TaskProcess(multiprocessing.Process):
    """进程类, 不同的进程可以用不同的初始化参数.

    这个类将资源的初始化工作放到进程开始之后执行, 避免了进程间数据的拷贝.
    """

    def __init__(self, task_class, task_args, input_queue, output_queue):
        super().__init__()
        assert hasattr(task_class, "process")
        self.task_class = dill.dumps(task_class)
        self.task_args = dill.dumps(task_args)
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        task_class = dill.loads(self.task_class)
        task_args = dill.loads(self.task_args)
        if isinstance(task_args, tuple):
            task = task_class(*task_args)
        else:
            task = task_class(task_args)
        while True:
            sid, sample = self.input_queue.get()
            if sample is None: break
            if isinstance(sample, tuple):
                self.output_queue.put((sid, task.process(*sample)))
            else:
                self.output_queue.put((sid, task.process(sample)))


class ProxyTaskClass:
    """本类将函数转包装成类. 供TaskProcess使用."""

    def __init__(self, taskfun, args):
        self.args = args if isinstance(args, tuple) else (args,)
        self.taskfun = taskfun

    def process(self, *sample):
        return self.taskfun(*sample, *self.args)


class TaskPool:
    """带初始化的多进程Pool.

    原始的multiprocessing.Pool也支持初始化参数, 但是, 所有进程的初始化参数
    必须是一样的. 有时候我们需要不同的进程其初始化参数也不一样, 比如我们用
    多GPU对训练好的模型进行测试的时候, 我们希望不同的进程对应不同的GPU.
    这个类弥补了原生Pool类的不足.

    Args:
        task_class: 每一个进程开始时初始化的类名, 其必须有一个定义如下的
            成员函数: process(self, sample). 在调用这个函数时, 如果sample是
            tuple类型, 会将其展开.
        task_args: 一个args列表, 用来初始化task_class. 每一项对应一个进程.
            同样的, 如果task_args中的项为tuple类型, 会将其展开. 如果
            task_class的初始化函数不需要参数, 则task_args中的每一项为一个
            空的tuple.
    """

    def __init__(self, task_class, task_args):
        assert hasattr(task_class, "process")
        # 这里task_args是一个参数列表, 其中的一项才是task_class的初始化参数
        assert isinstance(task_args, (tuple, list))
        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        # 如果线程数是1, 就直接串行处理
        self.is_single_thread = (len(task_args) <= 1)

        if self.is_single_thread:
            if isinstance(task_args[0], tuple):
                self.task_instance = task_class(*task_args[0])
            else:
                self.task_instance = task_class(task_args[0])
        else:
            self.processes = []
            for args in task_args:
                self.processes.append(
                    TaskProcess(task_class,
                                args,
                                self.input_queue,
                                self.output_queue))
                self.processes[-1].start()

    def process(self, samples, batch_size=0):
        """多进程批量处理函数, 类似于pool.map.

        如果samples个数太多, 一次性装入input_queue可能会导致内存不足.
        所以这里采用batch的方式: 当input_queue的大小小于batch_size的时候,
        就往里面装batch_size个样本. 不直接使用queue的阻塞机制是为了实时
        打印进度.
        """

        if self.is_single_thread:
            results = []
            start_time = time.time()
            for sid, sample in enumerate(samples, 1):
                if isinstance(sample, tuple):
                    results.append(self.task_instance.process(*sample))
                else:
                    results.append(self.task_instance.process(sample))
                if time.time() - start_time > 5:
                    logging.info("Progress (sequential) %d/%d",
                                 sid,
                                 len(samples))
                    start_time = time.time()
            return results

        samples = list(enumerate(samples))
        batch_size = batch_size or len(samples)
        num_samples = len(samples)

        # 装载首个batch
        batch_samples = samples[:batch_size]
        samples = samples[batch_size:]
        for sample in batch_samples:
            self.input_queue.put(sample)

        results = []
        start_time = time.time()
        while len(results) < num_samples:
            if self.input_queue.qsize() < batch_size and len(samples) != 0:
                if self.input_queue.empty():
                    # 这里提醒一下要提高batch_size
                    logging.warning("input queue is empty, time wasted.")
                batch_samples = samples[:batch_size]
                samples = samples[batch_size:]
                for sample in batch_samples:
                    self.input_queue.put(sample)
            while not self.output_queue.empty():
                results.append(self.output_queue.get())
            if len(results) < num_samples:
                time.sleep(1)  # 这里sleep的时间不能过长
            if time.time() - start_time > 5:
                logging.info("Progress (threads %d) %d/%d",
                             len(self.processes),
                             len(results),
                             num_samples)
                start_time = time.time()

        results.sort(key=lambda x: x[0])
        results = list(list(zip(*results))[1])
        return results

    def finish(self):
        assert self.output_queue.empty(), \
            "Internal error: output queue must be empty."

        if self.is_single_thread: return None

        # 传递None让子进程退出
        for proc in self.processes:
            self.input_queue.put((None, None))
        while not self.input_queue.empty():
            time.sleep(1)

        # 必须保证子进程中的queue都为空, 否则会造成死锁
        for proc in self.processes:
            proc.join()
        return None

    @staticmethod
    def get_pool(numthreads, taskfun, args=tuple()):
        """函数版本的multiprocessing.Pool.

        taskfun (function): 只能为全局函数或者类中的staticmethod, 函数定义
            如下: taskfun(sample, args), 如果sample或者args为tuple, 则将其
            展开: taskfun(*sample, *args).
        """
        return TaskPool(ProxyTaskClass, [(taskfun, args)] * numthreads)

    @staticmethod
    def map(numthreads, taskfun, samples, args=tuple(), batch_size=0):
        """函数版本的map. 参数请参考get_pool."""

        pool = TaskPool.get_pool(numthreads, taskfun, args)
        results = pool.process(samples, batch_size)
        pool.finish()
        return results


if __name__ == "__main__":
    pass
