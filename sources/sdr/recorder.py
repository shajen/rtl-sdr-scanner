#!/usr/bin/python3

import logging
import wave
import datetime
import os
import numpy as np
import scipy.signal as signal
import sdr.tools
import time as _time
import queue
import threading
import multiprocessing
import math


def decode_fm(data, frequency, center_frequency, bandwidth, **kwargs):
    frequency_offset = frequency - center_frequency
    Fs = bandwidth
    data *= np.exp(-1.0j * 2.0 * np.pi * frequency_offset / bandwidth * np.arange(data.size))

    f_bw = 100000
    n_taps = 4
    lpf = signal.remez(n_taps, [0, f_bw, f_bw + (Fs / 2 - f_bw) / 4, Fs / 2], [1, 0], Hz=Fs)
    x3 = signal.lfilter(lpf, 1.0, data)

    dec_rate = int(Fs / f_bw)
    x4 = x3[0::dec_rate]
    Fs_y = Fs / dec_rate

    y5 = x4[1:] * np.conj(x4[:-1])
    x5 = np.angle(y5)

    d = Fs_y * 75e-6  # Calculate the # of samples to hit the -3dB point
    x = np.exp(-1 / d)  # Calculate the decay between each sample
    b = [1 - x]  # Create the filter coefficients
    a = [1, -x]
    x6 = signal.lfilter(b, a, x5)

    audio_freq = kwargs["wav_sample_rate"]
    dec_audio = int(Fs_y / audio_freq)
    sample_rate = Fs_y / dec_audio

    x7 = signal.decimate(x6, dec_audio)
    x7 *= 100000 / np.max(np.abs(x7))

    return (sample_rate, x7.astype("int16"))


def decode_fm_to_wav(data, filename, frequency, center_frequency, bandwidth, **kwargs):
    file = wave.open(filename, "wb")
    file.setnchannels(1)
    file.setsampwidth(2)
    (sample_rate, _data) = decode_fm(data, frequency, center_frequency, bandwidth, **kwargs)
    file.setframerate(sample_rate)
    file.writeframes(_data)
    file.close()


class Recording:
    def __init__(self, start, stop, bandwidth, **kwargs):
        self.__start = start
        self.__stop = stop
        self.__bandwidth = bandwidth
        self.__samples = []
        self.__samples_time = []
        self.__time_start = 0
        self.__time_end = 0
        self.__time_last_data = 0
        self.__frequencies = []
        self.__min_recording_time = kwargs["min_recording_time"]
        self.__max_recording_time = kwargs["max_recording_time"]
        self.__max_silence_time = kwargs["max_silence_time"]

    def __duration(self):
        if self.__time_last_data == 0:
            return 0.0
        else:
            return self.__time_last_data - self.__time_start

    def info(self, **kwargs):
        if "frequency" in kwargs:
            frequency = kwargs["frequency"]
        else:
            frequency = int(self.__frequency())

        if "duration" in kwargs:
            time = kwargs["duration"]
        else:
            time = self.__duration()

        if "wav_size" in kwargs:
            size_label = "wav size"
            size = kwargs["wav_size"]
        else:
            size_label = "raw size"
            size = self.size()

        return "recording %s, %s, time: %.2f s, %s: %.2f MB" % (
            sdr.tools.format_frequency(frequency),
            sdr.tools.format_frequency_range(self.__start, self.__stop),
            time,
            size_label,
            size / 1024 / 1024,
        )

    def __frequency(self):
        if len(self.__frequencies) % 2 == 0:
            frequencies = [frequency for (frequency, power, time) in self.__frequencies[:-1]]
        else:
            frequencies = [frequency for (frequency, power, time) in self.__frequencies]
        return int(np.median(frequencies))

    def size(self):
        if self.__samples:
            return len(self.__samples) * self.__samples[0].nbytes
        else:
            return 0

    def process(self, **kwargs):
        logger = logging.getLogger("recorder")
        frequency = self.__frequency()
        if self.__duration() <= self.__min_recording_time:
            logger.info("removing (too short) %s" % self.info())
        else:
            n = self.__samples_time.index(self.__time_last_data)
            data = np.array(self.__samples[:n]).flatten()
            center_frequency = (self.__start + self.__stop) // 2
            logger.info("start processing %s" % self.info())

            now = datetime.datetime.fromtimestamp(self.__time_start)
            dir = "%s/%04d-%02d-%02d" % (kwargs["wav_directory"], now.year, now.month, now.day)
            os.makedirs(dir, exist_ok=True)
            filename = "%s/%02d_%02d_%02d_%09d.wav" % (dir, now.hour, now.minute, now.second, frequency)

            thread = multiprocessing.Process(target=decode_fm_to_wav, args=(data, filename, frequency, center_frequency, self.__bandwidth), kwargs=kwargs)
            thread.start()
            thread.join()

            with wave.open(filename, "rb") as file:
                duration = file.getnframes() / float(file.getframerate())
            size = os.path.getsize(filename)
            if duration <= self.__min_recording_time:
                logger.info("removing (too short) %s" % self.info(duration=duration, wav_size=size))
                os.remove(filename)
            else:
                logger.info("finished processing %s" % self.info(duration=duration, wav_size=size))

    def add_samples(self, samples, time):
        if self.__time_start == 0:
            self.__time_start = time
        if self.__time_last_data == 0:
            self.__time_last_data = time
        self.__time_end = time
        self.__samples.append(samples)
        self.__samples_time.append(time)

    def add_frequency(self, frequency, power, time):
        self.__frequencies.append((frequency, power, time))

    def set_time_last_data(self, time):
        self.__time_last_data = time

    def finished(self):
        return self.__time_last_data + self.__max_silence_time < self.__time_end or self.__time_last_data - self.__time_start >= self.__max_recording_time


class Recoder:
    class Data:
        def __init__(self):
            self.is_running = True

    def __init__(self, **kwargs):
        self.__recording = None
        self.__recordings = queue.Queue()
        self.__data = Recoder.Data()
        self.__thread = threading.Thread(target=Recoder.__run, args=(self.__recordings, self.__data), kwargs=kwargs)
        self.__thread.start()

    def stop(self):
        self.__data.is_running = False
        self.__thread.join()

    @staticmethod
    def __run(queue, data, **kwargs):
        while data.is_running:
            if queue.empty():
                _time.sleep(0.1)
            else:
                try:
                    queue.get().process(**kwargs)
                except Exception as e:
                    logger = logging.getLogger("recorder")
                    logger.warning("exception during recording processing: %s" % e)

    def record(self, data, time, frequencies, powers, _range, **kwargs):
        start = _range["start"]
        stop = _range["stop"]
        step = _range["step"]
        bandwidth = _range["bandwidth"]
        logger = logging.getLogger("recorder")

        if self.__recording is None:
            i = np.argmax(powers)
            if powers[i] > float(kwargs["noise_level"]):
                frequency = frequencies[i]
                bandwidth = _range["step"]
                while bandwidth * 2 <= kwargs["recording_max_bandwidth"]:
                    bandwidth = bandwidth * 2
                offset = kwargs["recording_frequency_shift"]
                start = int(frequency - offset - bandwidth // 2)
                stop = int(frequency - offset + bandwidth // 2)
                self.__recording = Recording(start, stop, bandwidth, **kwargs)
                self.__recording.add_frequency(frequencies[i], powers[i], time)
                logger.info("start %s" % self.__recording.info(frequency=int(frequencies[i])))
                return {"start": start, "stop": stop, "step": step, "bandwidth": bandwidth}
        else:
            index = np.where(powers > float(kwargs["noise_level"]))[0]
            if index.size != 0:
                self.__recording.set_time_last_data(time)
                for i in index:
                    self.__recording.add_frequency(frequencies[i], powers[i], time)

            self.__recording.add_samples(data, time)

            if self.__recording.finished() or self.__recording.size() > (kwargs["buffer_size_mb"] * 1024 * 1024):
                logger.info("finish %s" % self.__recording.info())
                self.__recordings.put(self.__recording)
                self.__recording = None
                return None

            return _range
