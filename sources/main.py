#!/usr/bin/python3

import argparse
import datetime
import json
import logging
import os
import sdr.scanner


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="path to config file", type=str, metavar="file")
    parser.add_argument("-lf", "--log_frequencies", help="print n best signals per range", type=int, default=3, metavar="n")
    parser.add_argument("-ld", "--log_directory", help="store output log in directory", type=str, metavar="dir")
    parser.add_argument("-wd", "--wav_directory", help="store output wav in directory", type=str, metavar="dir", default="wav")
    parser.add_argument("-dr", "--disable_recording", help="disable recording, only scannig", action="store_true")
    parser.add_argument("-z", "--show_zero_signal", help="print zero signal if not found any better", action="store_true")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    config_logger(args.verbose, args.log_directory)
    with open(args.config) as f:
        config = json.load(f)
        sdr.scanner.run(
            frequencies_ranges=config["frequencies_ranges"],
            ignored_frequencies_ranges=config["ignored_frequencies_ranges"],
            ppm_error=int(config["device"]["ppm_error"]),
            tuner_gain=config["device"]["tuner_gain"],
            squelch=config["recording"]["squelch"],
            bandwidth=config["scanning"]["bandwidth"],
            noise_level=config["scanning"]["noise_level"],
            samples=config["scanning"]["samples"],
            fft=config["scanning"]["fft"],
            min_recording_time=config["recording"]["min_recording_time"],
            max_recording_time=config["recording"]["max_recording_time"],
            max_silence_time=config["recording"]["max_silence_time"],
            show_zero_signal=args.show_zero_signal,
            log_frequencies=args.log_frequencies,
            wav_directory=args.wav_directory,
            disable_recording=args.disable_recording,
        )
