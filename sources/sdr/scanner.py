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

    device.center_freq = (start + stop) // 2
    [powers, frequencies] = matplotlib.mlab.psd(device.read_samples(samples), NFFT=fft, Fs=device.sample_rate)
    return frequencies + device.center_freq, np.log10(powers)


def __detect_best_signal(frequencies, powers, sorted_frequencies_indexes, **kwargs):
    index = len(powers) // 2
    if sorted_frequencies_indexes[0] == index:
        return (int(frequencies[index]), float(powers[index]), 0, False)

    ignored_frequencies_ranges = kwargs["ignored_frequencies_ranges"]
    for i in sorted_frequencies_indexes:
        if not any(_range["start"] <= frequencies[i] and frequencies[i] <= _range["stop"] for _range in ignored_frequencies_ranges):
            return (int(frequencies[i]), float(powers[i]), 12500, True)

    return (0, -100.0, 0, False)


def __scan(device, **kwargs):
    logger = logging.getLogger("sdr")
    print_best_frequencies = kwargs["print_best_frequencies"]
    filter_best_frequencies = kwargs["filter_best_frequencies"]
    bandwidth = kwargs["bandwidth"]
    disable_recording = kwargs["disable_recording"]
    ignored_frequencies_ranges = kwargs["ignored_frequencies_ranges"]

    noise_levels = []
    best_frequencies = np.zeros(shape=0, dtype=np.int)
    best_powers = np.zeros(shape=0, dtype=np.float)
    for _range in kwargs["frequencies_ranges"]:
        start = _range["start"]
        stop = _range["stop"]
        for substart in range(start, stop, bandwidth):
            frequencies, powers = __get_frequency_power(device, substart, substart + bandwidth, **kwargs)
            sorted_frequencies_indexes = np.argsort(powers)[::-1]
            (frequency, _, width, recording) = __detect_best_signal(frequencies, powers, sorted_frequencies_indexes, **kwargs)

            index = len(powers) // 2
            if sorted_frequencies_indexes[0] == index:
                noise_levels.append(powers[index])
            else:
                noise_levels.append(-100)
            best_frequencies = np.concatenate((best_frequencies, frequencies[sorted_frequencies_indexes[:print_best_frequencies]]))
            best_powers = np.concatenate((best_powers, powers[sorted_frequencies_indexes[:print_best_frequencies]]))

            if recording and not disable_recording:
                sdr.recorder.record(device, frequency, width, _range, **kwargs)

    indexes = np.argsort(best_powers)[::-1][:print_best_frequencies]
    best_frequencies = best_frequencies[indexes]
    best_powers = best_powers[indexes]
    indexes = np.argsort(best_frequencies)
    best_frequencies = best_frequencies[indexes]
    best_powers = best_powers[indexes]
    if filter_best_frequencies:
        if -100 in noise_levels:
            noise_level = -100
        else:
            noise_level = np.max(noise_levels)
    else:
        noise_level = -100
    for i in range(len(best_frequencies)):
        if noise_level < best_powers[i]:
            logger.debug(sdr.tools.format_frequnecy_power(int(best_frequencies[i]), float(best_powers[i])))


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
