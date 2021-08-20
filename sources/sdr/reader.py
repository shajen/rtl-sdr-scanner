#!/usr/bin/python3

import threading
import time
import logging


class Reader:
    class Data:
        def __init__(self):
            self.is_running = True
            self.range = None
            self.force = False

    def __init__(self, queue, device, **kwargs):
        self.__device = device
        self.__data = Reader.Data()
        self.__thread = threading.Thread(target=self.__run, args=(device, queue, self.__data))
        self.__thread.start()

    def stop(self):
        self.__data.is_running = False
        self.__thread.join()

    @staticmethod
    def __run(device, queue, data):
        while data.is_running:
            if data.range is not None and data.range["start"] != 0 and data.range["stop"] != 0:
                _range = data.range
                frequency = (_range["stop"] + _range["start"]) // 2
                if device.center_freq != frequency:
                    device.center_freq = frequency
                    device.bandwidth = _range["bandwidth"]
                    device.sample_rate = _range["bandwidth"]
                if data.force:
                    samples = _range["bandwidth"] // 4
                else:
                    samples = _range["bandwidth"] // 20
                _time = time.time()
                _data = device.read_samples(samples)
                if data.force and _range["start"] != data.range["start"] and _range["stop"] != data.range["stop"]:
                    continue
                queue.put((_data, _time, _range))
            else:
                time.sleep(0.01)

    def set_frequency(self, _range, force):
        self.__data.range = _range
        self.__data.force = force
