#!/usr/bin/python3

import argparse
import datetime
import json
import logging
import os
import sdr.scanner
import sdr.tools
import signal
import subprocess
import sys
import time


def config_logger(verbose, dir):
    params = {}

    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(len(levels) - 1, verbose)]

    params["format"] = "[%(asctime)s][%(levelname)7s][%(name)6s] %(message)s"
    params["level"] = level
    params["datefmt"] = "%Y-%m-%d %H:%M:%S"

    if dir:
        now = datetime.datetime.now()
        os.makedirs("%s/%04d-%02d-%02d" % (dir, now.year, now.month, now.day), exist_ok=True)
        filename = "%s/%04d-%02d-%02d/%02d_%02d_%02d.txt" % (dir, now.year, now.month, now.day, now.hour, now.minute, now.second)
        params["filename"] = filename
    logging.basicConfig(**params)


def separator(label, **kwargs):
    length = kwargs.get("length", 80)
    logger = logging.getLogger("main")

    l1 = int((length - len(label) - 2) / 2)
    l2 = (l1 + 1) if len(label) % 2 else l1
    logger.info("")
    logger.info("#" * length)
    logger.info("%s %s %s" % ("#" * l1, label.upper(), "#" * l2))
    logger.info("#" * length)


def print_ignored_frequencies(**kwargs):
    separator("ignored frequencies")
    logger = logging.getLogger("main")
    ignored_exact_frequencies = kwargs["ignored_exact_frequencies"]
    ignored_ranges_frequencies = kwargs["ignored_ranges_frequencies"]
    ignored_found_frequencies = kwargs["ignored_found_frequencies"]

    for frequnecy in ignored_exact_frequencies:
        logger.info("ignored frequency user defined: %s" % sdr.tools.format_frequnecy(frequnecy))
    for [start, stop] in ignored_ranges_frequencies:
        logger.info("ignored frequency range user defined: %s" % (sdr.tools.format_frequnecy_range(start, stop)))
    for frequnecy in ignored_found_frequencies:
        logger.info("ignored frequency found: %s" % sdr.tools.format_frequnecy(frequnecy))


def print_frequencies_ranges(**kwargs):
    separator("scanning ranges")
    logger = logging.getLogger("main")
    frequencies_ranges = kwargs["frequencies_ranges"]

    for range in frequencies_ranges:
        start = range["start"]
        stop = range["stop"]
        step = range["step"]
        logger.info("scanned frequency range: %s" % (sdr.tools.format_frequnecy_range(start, stop, step)))


def record(frequency, **kwargs):
    logger = logging.getLogger("main")
    logger.info("start recording frequnecy: %s" % sdr.tools.format_frequnecy(frequency))
    rate = str(kwargs["rate"])
    modulation = kwargs["modulation"]
    ppm_error = str(kwargs["ppm_error"])
    squelch = str(kwargs["squelch"])
    dir = kwargs["dir"]
    timeout = kwargs["timeout"]

    now = datetime.datetime.now()
    dir = "%s/%04d-%02d-%02d" % (dir, now.year, now.month, now.day)
    os.makedirs(dir, exist_ok=True)
    filename = "%s/%02d_%02d_%02d_%09d.wav" % (dir, now.hour, now.minute, now.second, frequency)

    p1 = subprocess.Popen(
        ["rtl_fm", "-p", ppm_error, "-g", "0", "-M", modulation, "-f", str(frequency), "-s", rate, "-l", squelch],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    p2 = subprocess.Popen(
        ["sox", "-t", "raw", "-e", "signed", "-c", "1", "-b", "16", "-r", rate, "-", filename],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    factor = 4
    time.sleep(1 / factor)
    last_size = 0
    for _ in range(timeout * factor):
        size = os.path.getsize(filename)
        if size == last_size:
            break
        else:
            last_size = size
        time.sleep(1 / factor)

    p1.terminate()
    p2.terminate()
    p1.wait()
    p2.wait()
    logger.info("stop recording frequnecy: %s" % sdr.tools.format_frequnecy(frequency))

    if size <= 100:
        os.remove(filename)
        logger.warning("recording too short, removing")


def scan(**kwargs):
    logger = logging.getLogger("main")
    ppm_error = kwargs["ppm_error"]
    wav_dir = kwargs["wav_dir"]
    config = kwargs["config"]
    ignored_ranges_frequencies = kwargs["ignored_ranges_frequencies"]
    ignored_exact_frequencies = kwargs["ignored_exact_frequencies"]
    ignored_found_frequencies = kwargs["ignored_found_frequencies"]
    rate = config["rate"]
    squelch = config["squelch"]
    timeout = config["timeout"]

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
        if args.log_frequencies > 0:
            for (frequency, power) in frequency_power[-args.log_frequencies :]:
                logger.debug(sdr.tools.format_frequnecy_power(frequency, power))
        if frequency_power:
            (frequency, power) = frequency_power[-1]
            record(frequency, rate=rate, modulation=modulation, ppm_error=ppm_error, squelch=squelch, dir=wav_dir, timeout=timeout)
        elif args.show_zero_signal:
            logger.info(sdr.tools.format_frequnecy_power(0, 0))


class ApplicationKiller:
    is_running = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum, frame):
        logger = logging.getLogger("main")
        logger.warning("stopping application")
        self.is_running = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="path to config file", type=str, metavar="file")
    parser.add_argument("-lf", "--log_frequencies", help="print n best signals per range", type=int, default=3, metavar="n")
    parser.add_argument("-ld", "--log_directory", help="store output log in directory", type=str, metavar="dir")
    parser.add_argument("-wd", "--wav_directory", help="store output wav in directory", type=str, metavar="dir", default="wav")
    parser.add_argument("-z", "--show_zero_signal", help="print zero signal if not found any better", action="store_true")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    config_logger(args.verbose, args.log_directory)
    with open(args.config) as f:
        config = json.load(f)

        ppm_error = int(config["ppm_error"])

        ignored_ranges_frequencies = config["ignored_frequencies"]["ranges"]
        ignored_exact_frequencies = config["ignored_frequencies"]["exact"]
        ignored_found_frequencies = sdr.scanner.get_ignored_frequencies(
            ppm_error=ppm_error,
            frequencies_ranges=config["frequencies_ranges"],
            count=config["ignored_frequencies"]["scan"]["count"],
            mode=config["ignored_frequencies"]["scan"]["mode"],
            sleep=config["ignored_frequencies"]["scan"]["sleep"],
        )

        print_ignored_frequencies(
            ignored_ranges_frequencies=ignored_ranges_frequencies,
            ignored_exact_frequencies=ignored_exact_frequencies,
            ignored_found_frequencies=ignored_found_frequencies,
        )
        print_frequencies_ranges(frequencies_ranges=config["frequencies_ranges"])
        separator("scanning started")

        killer = ApplicationKiller()
        while killer.is_running:
            scan(
                ppm_error=ppm_error,
                config=config,
                wav_dir=args.wav_directory,
                ignored_ranges_frequencies=ignored_ranges_frequencies,
                ignored_exact_frequencies=ignored_exact_frequencies,
                ignored_found_frequencies=ignored_found_frequencies,
            )
