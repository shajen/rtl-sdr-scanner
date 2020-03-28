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


def __get_frequency_power(device, config, **kwargs):
    start = config["start"]
    stop = config["stop"]
    samples = kwargs["samples"]
    fft = kwargs["fft"]

    device.sample_rate = stop - start
    device.center_freq = int((start + stop) / 2)
    [powers, frequencies] = matplotlib.mlab.psd(device.read_samples(samples), NFFT=fft, Fs=device.sample_rate)
    return frequencies + device.center_freq, np.log10(powers)


def __scan(device, **kwargs):
    logger = logging.getLogger("sdr")
    log_frequencies = kwargs["log_frequencies"]
    show_zero_signal = kwargs["show_zero_signal"]
    noise_level = kwargs["noise_level"]
    disable_recording = kwargs["disable_recording"]

    for _config in kwargs["frequencies_ranges"]:
        frequencies, powers = __get_frequency_power(device, _config, **kwargs)
        best_frequencies = np.argsort(powers)
        for i in best_frequencies[-log_frequencies:]:
            if noise_level <= powers[i]:
                logger.debug(sdr.tools.format_frequnecy_power(int(frequencies[i]), float(powers[i])))
        if show_zero_signal:
            logger.debug(sdr.tools.format_frequnecy_power(0, 0))

        if not disable_recording:
            frequency = int(frequencies[best_frequencies[-1]])
            power = int(powers[best_frequencies[-1]])
            if noise_level <= power:
                sdr.recorder.record(device, frequency, 25000, _config, **kwargs)


def run(**kwargs):
    sdr.tools.print_ignored_frequencies(
        ignored_ranges_frequencies=kwargs["ignored_ranges_frequencies"],
        ignored_exact_frequencies=kwargs["ignored_ranges_frequencies"],
        ignored_found_frequencies=[],
    )
    sdr.tools.print_frequencies_ranges(frequencies_ranges=kwargs["frequencies_ranges"])
    sdr.tools.separator("scanning started")

    device = rtlsdr.RtlSdr()
    device.ppm_error = kwargs["ppm_error"]
    device.gain = kwargs["tuner_gain"]

    killer = application_killer.ApplicationKiller()
    while killer.is_running:
        __scan(device, **kwargs)
