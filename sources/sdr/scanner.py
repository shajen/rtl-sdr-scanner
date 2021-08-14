#!/usr/bin/python3


import application_killer
import logging
import math
import rtlsdr
import sdr.tools
import sdr.samples_reader
import sdr.samples_analyser
import queue


def __filter_ranges(**kwargs):
    ranges = []
    logger = logging.getLogger("sdr")
    bandwidth = kwargs["bandwidth"]
    for _range in kwargs["frequencies_ranges"]:
        start = _range["start"]
        stop = _range["stop"]
        if (stop - start) % bandwidth != 0:
            _range["stop"] = start + (bandwidth * math.ceil((stop - start) / bandwidth))
            logger.warning(
                "frequency range: %s error! range not fit to bandwidth: %s! adjusting range end to %s!",
                sdr.tools.format_frequency_range(start, stop),
                sdr.tools.format_frequency(bandwidth),
                sdr.tools.format_frequency(_range["stop"]),
            )
        ranges.append(_range)
    if ranges:
        return ranges
    else:
        logger.error("empty frequency ranges! quitting!")
        exit(1)


def run(**kwargs):
    sdr.tools.print_ignored_frequencies(kwargs["ignored_frequencies_ranges"])
    sdr.tools.print_frequencies_ranges(kwargs["frequencies_ranges"])
    sdr.tools.separator("scanning started")
    kwargs["frequencies_ranges"] = __filter_ranges(**kwargs)
    bandwidth = kwargs["bandwidth"]
    try:
        device = rtlsdr.RtlSdr()
        device.ppm_error = kwargs["ppm_error"]
        device.gain = kwargs["tuner_gain"]
        device.sample_rate = bandwidth
        _queue = queue.Queue()
        killer = application_killer.ApplicationKiller()
        samplesReader = sdr.samples_reader.SamplesReader(_queue, device, **kwargs)
        samplesAnalyser = sdr.samples_analyser.SamplesAnalyser(_queue, **kwargs)
        samplesReader.start()
        while killer.is_running:
            for _range in kwargs["frequencies_ranges"]:
                for substart in range(_range["start"], _range["stop"], bandwidth):
                    samplesReader.set_frequency(substart, substart + bandwidth)
                while samplesAnalyser.analyse(**kwargs) and killer.is_running:
                    pass
        samplesReader.stop()

    except rtlsdr.rtlsdr.LibUSBError as e:
        logger = logging.getLogger("sdr")
        logger.critical("Device error, error message: " + str(e) + " quitting!")
        exit(1)
