#!/usr/bin/python3


import application_killer
import datetime
import logging
import matplotlib.mlab
import numpy as np
import os
import rtlsdr
import sdr.recorder
import sdr.tools


def __get_frequency_power(device, start, stop, **kwargs):
    samples = kwargs["samples"]
    fft = kwargs["fft"]

    device.center_freq = int((start + stop) / 2)
    [powers, frequencies] = matplotlib.mlab.psd(device.read_samples(samples), NFFT=fft, Fs=device.sample_rate)
    return frequencies + device.center_freq, np.log10(powers)


def __detect_best_signal(frequencies, powers, sorted_frequencies_indexes, **kwargs):
    noise_level = kwargs["noise_level"]
    ignored_frequencies_ranges = kwargs["ignored_frequencies_ranges"]

    for i in sorted_frequencies_indexes:
        if not any(_range["start"] <= frequencies[i] and frequencies[i] <= _range["stop"] for _range in ignored_frequencies_ranges):
            return (int(frequencies[i]), float(powers[i]), 25000, noise_level <= powers[i])
    return (0, -100.0, 0, False)


def __scan(device, **kwargs):
    logger = logging.getLogger("sdr")
    log_frequencies = kwargs["log_frequencies"]
    disable_best_frequency = kwargs["disable_best_frequency"]
    bandwidth = kwargs["bandwidth"]
    disable_recording = kwargs["disable_recording"]
    noise_level = kwargs["noise_level"]
    ignored_frequencies_ranges = kwargs["ignored_frequencies_ranges"]

    printed_any_frequency = False
    best_frequency = 0
    best_power = -100.0
    for _range in kwargs["frequencies_ranges"]:
        start = _range["start"]
        stop = _range["stop"]
        for substart in range(start, stop, bandwidth):
            frequencies, powers = __get_frequency_power(device, substart, substart + bandwidth, **kwargs)
            sorted_frequencies_indexes = np.argsort(powers)[::-1]
            (frequency, power, width, recording) = __detect_best_signal(frequencies, powers, sorted_frequencies_indexes, **kwargs)

            if recording and not disable_recording:
                sdr.recorder.record(device, frequency, width, _range, **kwargs)

            if best_power < power:
                best_frequency = frequency
                best_power = power

            for i in sorted_frequencies_indexes[:log_frequencies][::-1]:
                if noise_level <= powers[i]:
                    printed_any_frequency = True
                    logger.debug(sdr.tools.format_frequnecy_power(int(frequencies[i]), float(powers[i])))
                else:
                    break

    if not disable_best_frequency and not printed_any_frequency:
        logger.debug(sdr.tools.format_frequnecy_power(best_frequency, best_power))


def __filter_ranges(**kwargs):
    ranges = []
    logger = logging.getLogger("sdr")
    bandwidth = kwargs["bandwidth"]
    for _range in kwargs["frequencies_ranges"]:
        start = _range["start"]
        stop = _range["stop"]
        if (stop - start) % bandwidth != 0:
            logger.warning(
                "frequency range: %s error! range not fit to bandwidth: %s! skipping!"
                % (sdr.tools.format_frequnecy_range(start, stop), sdr.tools.format_frequnecy(bandwidth))
            )
        else:
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

    device = rtlsdr.RtlSdr()
    device.ppm_error = kwargs["ppm_error"]
    device.gain = kwargs["tuner_gain"]
    device.sample_rate = kwargs["bandwidth"]

    killer = application_killer.ApplicationKiller()
    while killer.is_running:
        __scan(device, **kwargs)
