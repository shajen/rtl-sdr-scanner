#!/usr/bin/python3

import application_killer
import argparse
import datetime
import json
import logging
import os
import sdr.scanner
import sdr.tools


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

        killer = application_killer.ApplicationKiller()
        while killer.is_running:
            sdr.scanner.scan(
                ppm_error=ppm_error,
                config=config,
                wav_dir=args.wav_directory,
                ignored_ranges_frequencies=ignored_ranges_frequencies,
                ignored_exact_frequencies=ignored_exact_frequencies,
                ignored_found_frequencies=ignored_found_frequencies,
                log_frequencies=args.log_frequencies,
                show_zero_signal=args.show_zero_signal,
            )
