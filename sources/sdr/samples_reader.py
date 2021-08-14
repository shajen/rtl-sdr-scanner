#!/usr/bin/python3

import threading
import time


class SamplesReader(threading.Thread):
    def __init__(self, queue, device, **kwargs):
        threading.Thread.__init__(self)
        self.__queue = queue
        self.__device = device
        self.__samples = kwargs["samples"]
        self.__is_running = True
        self.__start = 0
        self.__stop = 0

    def run(self):
        while self.__is_running:
            if self.__start != 0 and self.__stop != 0:
                frequency = (self.__stop + self.__start) // 2
                if self.__device.center_freq != frequency:
                    self.__device.center_freq = frequency
                self.__queue.put((self.__device.read_samples(self.__samples), self.__start, self.__stop))
            else:
                time.sleep(0.1)

    def stop(self):
        self.__is_running = False

    def set_frequency(self, start, stop):
        self.__start = start
        self.__stop = stop
