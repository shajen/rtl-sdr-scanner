#!/usr/bin/python3

import logging
import wave
import datetime
import os
import numpy as np
import scipy.signal as signal
import sdr.tools
import time


class Recording:
    def __init__(self, frequency, **kwargs):
        logger = logging.getLogger("sdr")
        logger.info("new recording: %s" % sdr.tools.format_frequency(frequency))

        now = datetime.datetime.now()
        dir = "%s/%04d-%02d-%02d" % (kwargs["wav_directory"], now.year, now.month, now.day)
        os.makedirs(dir, exist_ok=True)
        filename = "%s/%02d_%02d_%02d_%09d.wav" % (dir, now.hour, now.minute, now.second, frequency)

        self.__file = wave.open(filename, "wb")
        self.__filename = filename
        self.__file.setnchannels(1)
        self.__file.setsampwidth(2)
        self.__file.setframerate(kwargs["samples_rate"])
        self.__frequency = frequency
        self.__last_data = time.time()
        self.__min_recording_time = kwargs["min_recording_time"]
        self.__max_recording_time = kwargs["max_recording_time"]
        self.__max_silence_time = kwargs["max_silence_time"]
        self.__frequencies = [frequency]
        self.__margin = kwargs["channel_width"] // 2
        self.__max_frequencies = kwargs["samples_count_to_adjust_frequency"]

    def __del__(self):
        logger = logging.getLogger("sdr")
        duration = self.__file.getnframes() / float(self.__file.getframerate())
        if duration <= self.__min_recording_time:
            logger.info("close recording: %s, time: %.2fs, too short, removing" % (sdr.tools.format_frequency(self.frequency()), duration))
            os.remove(self.__filename)
        else:
            logger.info("close recording: %s, time: %.2fs" % (sdr.tools.format_frequency(self.frequency()), duration))

    def append_data(self, data):
        self.__file.writeframes(data)

    def frequency(self):
        return self.__frequency

    def contains(self, frequency):
        return self.frequency() - self.__margin <= frequency and frequency <= self.frequency() + self.__margin

    def finished(self):
        duration = self.__file.getnframes() / float(self.__file.getframerate())
        return self.__last_data + self.__max_silence_time < time.time() or duration >= self.__max_recording_time

    def update_last_data(self):
        self.__last_data = time.time()

    def add_frequency(self, frequency):
        if len(self.__frequencies) < self.__max_frequencies:
            self.__frequencies.append(frequency)
            self.__frequency = int(np.average(self.__frequencies))


class SamplesDecoder:
    def __init__(self, **kwargs):
        self.__recordings = []

    def __add_recording(self, frequency, **kwargs):
        if not any(recording.contains(frequency) for recording in self.__recordings):
            self.__recordings.append(Recording(frequency, **kwargs))

    def __remove_inactive_recordings(self, **kwargs):
        self.__recordings = [recording for recording in self.__recordings if not recording.finished()]

    def __decode_data(self, data, frequency, start, stop, **kwargs):
        Fs = kwargs["bandwidth"]
        F_offset = frequency - ((stop + start) // 2)
        x1 = data
        fc1 = np.exp(-1.0j * 2.0 * np.pi * F_offset / Fs * np.arange(len(x1)))
        x2 = x1 * fc1

        f_bw = 200000
        n_taps = 128
        lpf = signal.remez(n_taps, [0, f_bw, f_bw + (Fs / 2 - f_bw) / 4, Fs / 2], [1, 0], Hz=Fs)
        x3 = signal.lfilter(lpf, 1.0, x2)

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

        audio_freq = kwargs["samples_rate"]
        dec_audio = int(Fs_y / audio_freq)

        x7 = signal.decimate(x6, dec_audio)
        x7 *= 10000 / np.max(np.abs(x7))

        return x7.astype("int16")

    def decode(self, data, frequencies, powers, start, stop, **kwargs):
        index = np.where(powers > float(kwargs["noise_level"]))[0]
        frequencies = frequencies[index]

        for frequency in frequencies:
            self.__add_recording(int(frequency), **kwargs)

        self.__remove_inactive_recordings(**kwargs)

        for recording in self.__recordings:
            for frequency in frequencies:
                if recording.contains(frequency):
                    recording.update_last_data()
                    recording.add_frequency(frequency)
            recording.append_data(self.__decode_data(data, recording.frequency(), start, stop, **kwargs))

        return not bool(self.__recordings)
