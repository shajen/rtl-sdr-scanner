#!/usr/bin/python3

import subprocess
import time
import logging
import sdr.tools


def get_nearest_frequency_power(**kwargs):
    frequency_power = []
    start = kwargs["start"]
    stop = kwargs["stop"]
    step = kwargs["step"]
    integration_interval = kwargs["integration_interval"]
    ppm_error = kwargs["ppm_error"]

    proc = subprocess.Popen(
        ["rtl_power", "-c", "0.25", "-f", "%s:%s:%s" % (start, stop, step), "-i", str(integration_interval), "-1", "-p", str(ppm_error),],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = proc.communicate()
    if not stdout:
        logger = logging.getLogger("sdr")
        logger.error("rtl_power error!")
        logger.error("Please ensure rtl_power command work!")
        exit(1)
    for line in stdout.decode("utf-8").strip().split("\n"):
        data = line.split(",")
        offset = 0
        _start = int(data[2])
        _stop = int(data[3])
        _step = float(data[4])
        _powers = data[6:]
        for power in _powers:
            frequency_power.append((_start + offset, float(power)))
            offset += _step
    return frequency_power


def get_exact_frequency_power(**kwargs):
    start = kwargs["start"]
    step = kwargs["step"]
    ignored_ranges_frequencies = kwargs["ignored_ranges_frequencies"]
    ignored_exact_frequencies = kwargs["ignored_exact_frequencies"]
    minimal_power = kwargs["minimal_power"]

    nearest_frequency = get_nearest_frequency_power(**kwargs)
    frequency_power = []
    frequency = start
    for ((frequency_left, power_left), (frequency_right, power_right)) in zip(nearest_frequency[::2], nearest_frequency[1::2]):
        while frequency < frequency_left:
            frequency += step
        if (
            frequency_left <= frequency
            and frequency <= frequency_right
            and frequency not in ignored_exact_frequencies
            and not any([start <= frequency and frequency <= stop for [start, stop] in ignored_ranges_frequencies])
        ):
            power = max(power_left, power_right)
            if minimal_power <= power:
                frequency_power.append((frequency, power))
    return frequency_power


def get_ignored_frequencies_from_range(**kwargs):
    start = kwargs["start"]
    stop = kwargs["stop"]
    step = kwargs["step"]
    count = kwargs["count"]
    sleep = kwargs["sleep"]
    mode = kwargs["mode"]

    logger = logging.getLogger("sdr")
    logger.debug(
        "scanning for ignored frequency in frequency range: %s - %s, step: %s"
        % (sdr.tools.format_frequnecy(start), sdr.tools.format_frequnecy(stop), sdr.tools.format_frequnecy(step))
    )

    if mode == "intersection":
        frequencies = set(range(start, stop + step, step))
    else:
        frequencies = set([])
    for i in range(count):
        if i != 0:
            time.sleep(sleep)
        new_frequencies = set(map(lambda d: d[0], get_exact_frequency_power(**kwargs)))
        if mode == "intersection":
            frequencies.intersection_update(new_frequencies)
        else:
            frequencies.update(new_frequencies)
        logger.debug("ignored frequencies found (%d): %s" % (len(frequencies), sdr.tools.format_frequnecies(sorted(frequencies))))
    return sorted(frequencies)


def get_ignored_frequencies(**kwargs):
    count = kwargs["count"]
    frequencies_ranges = kwargs["frequencies_ranges"]
    kwargs["ignored_ranges_frequencies"] = []
    kwargs["ignored_exact_frequencies"] = []

    if count <= 0:
        return []
    ignored_frequencies = []
    for range in frequencies_ranges:
        kwargs["start"] = range["start"]
        kwargs["stop"] = range["stop"]
        kwargs["step"] = range["step"]
        kwargs["minimal_power"] = range["minimal_power"]
        kwargs["integration_interval"] = range["integration_interval"]
        ignored_frequencies.extend(get_ignored_frequencies_from_range(**kwargs))

    return ignored_frequencies
