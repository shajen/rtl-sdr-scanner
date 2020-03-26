#!/usr/bin/python3

import subprocess
import time
import logging
import sdr.tools
import sdr.recorder


def get_nearest_frequency_power(**kwargs):
    frequency_power = []
    start = kwargs["start"]
    stop = kwargs["stop"]
    step = kwargs["step"]
    integration_interval = kwargs["integration_interval"]
    ppm_error = kwargs["ppm_error"]
    logger = logging.getLogger("sdr")

    try:
        proc = subprocess.Popen(
            ["rtl_power", "-c", "0.25", "-f", "%s:%s:%s" % (start, stop, step), "-i", str(integration_interval), "-1", "-p", str(ppm_error),],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(timeout=integration_interval + 5)
    except FileNotFoundError:
        logger.error("rtl_power not found! Please install rtl_sdr!")
        exit(1)
    except subprocess.TimeoutExpired:
        logger.error("rtl_power timeout! Please ensure rtl_power work!")
        exit(1)
    if not stdout:
        stderr = stderr.decode()
        if "user cancel" not in stderr.lower():
            logger.error("rtl_power error! Please ensure rtl_power work!")
            logger.error("exit code: %d" % proc.returncode)
            for line in stderr.split("\n"):
                logger.error("stderr: %s" % line)
            exit(1)
        exit(0)
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
    logger.debug("scanning for ignored frequency in frequency range: %s" % sdr.tools.format_frequnecy_range(start, stop, step))

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


def scan(**kwargs):
    logger = logging.getLogger("main")
    ppm_error = kwargs["ppm_error"]
    wav_dir = kwargs["wav_dir"]
    config = kwargs["config"]
    log_frequencies = kwargs["log_frequencies"]
    show_zero_signal = kwargs["show_zero_signal"]
    ignored_ranges_frequencies = kwargs["ignored_ranges_frequencies"]
    ignored_exact_frequencies = kwargs["ignored_exact_frequencies"]
    ignored_found_frequencies = kwargs["ignored_found_frequencies"]
    rate = config["rate"]
    squelch = config["squelch"]
    min_recording_time = config["min_recording_time"]
    max_recording_time = config["max_recording_time"]
    max_silence_time = config["max_silence_time"]

    for range in config["frequencies_ranges"]:
        start = range["start"]
        stop = range["stop"]
        step = range["step"]
        minimal_power = range["minimal_power"]
        integration_interval = range["integration_interval"]
        modulation = range["modulation"]

        frequency_power = sdr.scanner.get_exact_frequency_power(
            start=start,
            stop=stop,
            step=step,
            integration_interval=integration_interval,
            ppm_error=ppm_error,
            minimal_power=minimal_power,
            ignored_ranges_frequencies=ignored_ranges_frequencies,
            ignored_exact_frequencies=ignored_exact_frequencies + ignored_found_frequencies,
        )
        frequency_power = sorted(frequency_power, key=lambda d: d[1])
        if log_frequencies > 0:
            if frequency_power:
                for (frequency, power) in frequency_power[-log_frequencies:]:
                    logger.debug(sdr.tools.format_frequnecy_power(frequency, power))
            elif show_zero_signal:
                logger.debug(sdr.tools.format_frequnecy_power(0, 0))

        if frequency_power:
            (frequency, power) = frequency_power[-1]
            sdr.recorder.record(
                frequency,
                rate=rate,
                modulation=modulation,
                ppm_error=ppm_error,
                squelch=squelch,
                dir=wav_dir,
                min_recording_time=min_recording_time,
                max_recording_time=max_recording_time,
                max_silence_time=max_silence_time,
            )
