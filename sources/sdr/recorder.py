#!/usr/bin/python3

import datetime
import logging
import os
import sdr.tools
import subprocess
import time
import wave


def record(frequency, **kwargs):
    logger = logging.getLogger("sdr")
    logger.info("start recording frequnecy: %s" % sdr.tools.format_frequnecy(frequency))
    rate = str(kwargs["rate"])
    modulation = kwargs["modulation"]
    ppm_error = str(kwargs["ppm_error"])
    squelch = str(kwargs["squelch"])
    dir = kwargs["dir"]
    min_recording_time = kwargs["min_recording_time"]
    max_recording_time = kwargs["max_recording_time"]
    max_silence_time = kwargs["max_silence_time"]

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

    time.sleep(max_silence_time)
    last_size = -1
    for _ in range(max_recording_time):
        size = os.path.getsize(filename)
        if size == last_size:
            break
        else:
            last_size = size
        time.sleep(max_silence_time)

    logger.info("stop recording frequnecy: %s" % sdr.tools.format_frequnecy(frequency))
    p1.terminate()
    p2.terminate()
    p1.wait()
    p2.wait()

    with wave.open(filename, "r") as f:
        frames = f.getnframes()
        rate = f.getframerate()
        length = frames / float(rate)
        logger.info("recording time: %.2f seconds" % length)
        if length < min_recording_time:
            os.remove(filename)
            logger.warning("recording time too short, removing")
