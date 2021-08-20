#!/usr/bin/python3


import application_killer
import logging
import math
import rtlsdr
import sdr.tools
import sdr.reader
import sdr.analyser
import queue


def __filter_ranges(**kwargs):
    min_bandwidth = kwargs["min_bandwidth"]
    max_bandwidth = kwargs["max_bandwidth"]
    ranges = []

    for _range in kwargs["frequencies_ranges"]:
        start = _range["start"]
        stop = _range["stop"]
        step = _range["step"]
        if (stop - start) % step != 0:
            stop = start + (step * math.ceil((stop - start) / step))
        bandwidth = step
        while bandwidth < min_bandwidth:
            bandwidth = bandwidth * 2
        while bandwidth * 2 <= max_bandwidth and bandwidth < (stop - start):
            bandwidth = bandwidth * 2

        if stop - start <= bandwidth:
            ranges.append({"start": start, "stop": stop, "step": step, "bandwidth": bandwidth})
        else:
            substep = int(math.pow(10, math.floor(math.log(bandwidth, 10))))
            substep = substep * (bandwidth // substep)
            for substart in range(start, stop, substep):
                substop = min(substart + substep, stop)
                ranges.append({"start": substart, "stop": substop, "step": step, "bandwidth": bandwidth})
    return ranges


def run(**kwargs):
    sdr.tools.print_frequencies(kwargs["ignored_frequencies_ranges"], "ignored frequencies")
    sdr.tools.print_frequencies(kwargs["frequencies_ranges"], "scanning frequencies")
    kwargs["frequencies_ranges"] = __filter_ranges(**kwargs)
    sdr.tools.print_frequencies(kwargs["frequencies_ranges"], "corrected scanning frequencies")
    sdr.tools.separator("scanning started")
    try:
        device = rtlsdr.RtlSdr()
        device.ppm_error = kwargs["ppm_error"]
        device.gain = kwargs["tuner_gain"]
        _queue = queue.Queue()
        killer = application_killer.ApplicationKiller()
        reader = sdr.reader.Reader(_queue, device, **kwargs)
        analyser = sdr.analyser.Analyser(_queue, **kwargs)
        while killer.is_running:
            for _range in kwargs["frequencies_ranges"]:
                reader.set_frequency(_range, False)
                while killer.is_running:
                    result = analyser.analyse(**kwargs)
                    if result:
                        reader.set_frequency(result, True)
                    else:
                        break
        analyser.stop()
        reader.stop()
    except rtlsdr.rtlsdr.LibUSBError as e:
        logger = logging.getLogger("scanner")
        logger.critical("Device error, error message: " + str(e) + " quitting!")
        exit(1)
