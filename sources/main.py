#!/usr/bin/python3

import json
import sdr.tools
import sdr.scanner
import logging
import argparse


def config_logger(verbose):
    logging.getLogger("tensorflow").setLevel(logging.ERROR)
    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(len(levels) - 1, verbose)]
    logging.basicConfig(format="[%(asctime)s][%(levelname)7s][%(name)6s] %(message)s", level=level, datefmt="%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="path to config file", type=str, metavar="file")
    parser.add_argument("-lf", "--log_frequencies", help="print n best signals per range", type=int, default=3, metavar="n")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    config_logger(args.verbose)
    logger = logging.getLogger("main")
    with open(args.config) as f:
        config = json.load(f)

        integration_interval = int(config["integration_interval"])
        ppm_error = int(config["ppm_error"])

        ignored_frequencies = sdr.scanner.get_ignored_frequencies(
            ppm_error=ppm_error,
            frequencies_ranges=config["frequencies_ranges"],
            manual=config["ignored_frequencies"]["manual"],
            count=config["ignored_frequencies"]["scan"]["count"],
            mode=config["ignored_frequencies"]["scan"]["mode"],
            sleep=config["ignored_frequencies"]["scan"]["sleep"],
            integration_interval=config["ignored_frequencies"]["scan"]["integration_interval"],
        )

        for range in config["frequencies_ranges"]:
            start = range["start"]
            stop = range["stop"]
            step = range["step"]
            minimal_power = range["minimal_power"]
            logger.info(
                "scaning for active frequencies (%s - %s, step: %s)"
                % (sdr.tools.format_frequnecy(start), sdr.tools.format_frequnecy(stop), sdr.tools.format_frequnecy(step))
            )

        while True:
            for range in config["frequencies_ranges"]:
                start = range["start"]
                stop = range["stop"]
                step = range["step"]
                minimal_power = range["minimal_power"]

                frequency_power = sdr.scanner.get_exact_frequency_power(
                    start=start,
                    stop=stop,
                    step=step,
                    integration_interval=integration_interval,
                    ppm_error=ppm_error,
                    minimal_power=minimal_power,
                    ignored_frequencies=ignored_frequencies,
                )
                frequency_power = sorted(frequency_power, key=lambda d: d[1])
                if args.log_frequencies > 0:
                    for (frequency, power) in frequency_power[-args.log_frequencies : -1]:
                        logger.debug("frequnecy: %s, power: %5.2f dB" % (sdr.tools.format_frequnecy(frequency), power))
                for (frequency, power) in frequency_power[-1:]:
                    logger.info("frequnecy: %s, power: %5.2f dB" % (sdr.tools.format_frequnecy(frequency), power))
