#!/usr/bin/python3

import math
import logging


def colored(string, color=None, background=None, attrs=None):
    try:
        import termcolor

        return termcolor.colored(string, color, background)
    except:
        return string


def format_frequency(frequency):
    if frequency == 0:
        return "0 Hz"
    else:
        return "{:,d} Hz".format(frequency)


def format_frequency_power(frequency, power):
    return "frequency: %14s, power: %6.2f dB %s" % (format_frequency(frequency), power, format_power(power))


def format_frequnecies(frequencies):
    return ", ".join([format_frequency(f) for f in frequencies])


def format_frequency_range(start, stop, step=0, bandwidth=0):
    if step == 0 or bandwidth == 0:
        return "%s - %s" % (format_frequency(start), format_frequency(stop))
    else:
        return "%s - %s, step: %8s, bandwidth: %s" % (format_frequency(start), format_frequency(stop), format_frequency(step), format_frequency(bandwidth))


def format_bar(value, **kwargs):
    min_value = kwargs.get("min", 0)
    max_value = kwargs.get("max", 100)
    length = kwargs.get("length", 80)

    if math.isnan(value):
        n = 0
    elif value <= min_value:
        n = 0
    elif max_value <= value:
        n = length
    else:
        single = (max_value - min_value) / length
        n = round((value - min_value) / single)
    return "#" * n + "_" * (length - n)


def format_power(value):
    return format_bar(value, min=-10, max=0, length=40)


def separator(label, **kwargs):
    length = kwargs.get("length", 80)
    logger = logging.getLogger("sdr")

    l1 = int((length - len(label) - 2) / 2)
    l2 = (l1 + 1) if len(label) % 2 else l1
    logger.info("")
    logger.info("#" * length)
    logger.info("%s %s %s" % ("#" * l1, label.upper(), "#" * l2))
    logger.info("#" * length)


def print_frequencies(frequencies, label):
    separator(label)
    logger = logging.getLogger("sdr")
    for range in frequencies:
        if "step" in range and "bandwidth" in range:
            logger.info("frequency range: %s" % (format_frequency_range(range["start"], range["stop"], range["step"], range["bandwidth"])))
        else:
            logger.info("frequency range: %s" % (format_frequency_range(range["start"], range["stop"])))
