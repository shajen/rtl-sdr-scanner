#!/usr/bin/python3

import math
import logging


def colored(string, color=None, background=None, attrs=None):
    try:
        import termcolor

        return termcolor.colored(string, color, background)
    except:
        return string


def format_frequnecy(frequency):
    if frequency == 0:
        return "0 Hz"
    else:
        return "{:,d} Hz".format(frequency)


def format_frequnecy_power(frequency, power):
    return "frequnecy: %14s, power: %5.2f dB %s" % (format_frequnecy(frequency), power, format_power(power))


def format_frequnecies(frequencies):
    return ", ".join([format_frequnecy(f) for f in frequencies])


def format_frequnecy_range(start, stop, step=0):
    if step == 0:
        return "%s - %s" % (format_frequnecy(start), format_frequnecy(stop))
    else:
        return "%s - %s, step: %8s" % (format_frequnecy(start), format_frequnecy(stop), format_frequnecy(step))


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
    return format_bar(value, min=0, max=20, length=40)


def separator(label, **kwargs):
    length = kwargs.get("length", 80)
    logger = logging.getLogger("sdr")

    l1 = int((length - len(label) - 2) / 2)
    l2 = (l1 + 1) if len(label) % 2 else l1
    logger.info("")
    logger.info("#" * length)
    logger.info("%s %s %s" % ("#" * l1, label.upper(), "#" * l2))
    logger.info("#" * length)


def print_ignored_frequencies(ignored_frequencies_ranges):
    separator("ignored frequencies")
    logger = logging.getLogger("sdr")
    for range in ignored_frequencies_ranges:
        logger.info("ignored frequency range user defined: %s" % (format_frequnecy_range(range["start"], range["stop"])))


def print_frequencies_ranges(frequencies_ranges):
    separator("scanning ranges")
    logger = logging.getLogger("sdr")
    for range in frequencies_ranges:
        logger.info("scanned frequency range: %s" % (format_frequnecy_range(range["start"], range["stop"])))
