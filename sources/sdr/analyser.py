#!/usr/bin/python3

import matplotlib.mlab
import numpy as np
import logging
import math
import sdr.tools
import sdr.recorder
import scipy.signal as signal


class Analyser:
    def __init__(self, queue, **kwargs):
        self.__queue = queue
        self.__recoder = sdr.recorder.Recoder(**kwargs)

    def stop(self):
        self.__recoder.stop()

    def __get_frequency_power(self, data, start, stop, step, bandwidth, **kwargs):
        fft = int(math.pow(2, math.log(bandwidth / step, 2)))
        frequency = (stop + start) // 2
        [powers, frequencies] = matplotlib.mlab.psd(data[: (len(data) // 10)], NFFT=fft, Fs=bandwidth)
        return (frequencies + frequency), np.log10(powers)

    def __filter_frequencies(self, frequencies, ignored_frequencies_ranges, inclusive):
        is_ok = lambda frequency: not any(_range["start"] <= frequency and frequency <= _range["stop"] for _range in ignored_frequencies_ranges)
        if inclusive:
            mask = [not is_ok(frequency) for frequency in frequencies]
        else:
            mask = [is_ok(frequency) for frequency in frequencies]
        return np.arange(len(frequencies))[mask]

    def __analyse(self, data, _time, _range, **kwargs):
        start = _range["start"]
        stop = _range["stop"]
        step = _range["step"]
        bandwidth = _range["bandwidth"]
        logger = logging.getLogger("analyser")
        print_best_frequencies = kwargs["print_best_frequencies"]

        frequencies, powers = self.__get_frequency_power(data, start, stop, step, bandwidth, **kwargs)

        frequencies_index = signal.find_peaks(powers, width=kwargs["peak_width"])[0]
        frequencies = frequencies[frequencies_index]
        powers = powers[frequencies_index]

        frequencies_index = self.__filter_frequencies(frequencies, kwargs["frequencies_ranges"], True)
        frequencies = frequencies[frequencies_index]
        powers = powers[frequencies_index]

        frequencies_index = self.__filter_frequencies(frequencies, kwargs["ignored_frequencies_ranges"], False)
        frequencies = frequencies[frequencies_index]
        powers = powers[frequencies_index]

        if print_best_frequencies > 0:
            indexes = np.argsort(powers)[::-1][:print_best_frequencies]
            frequencies = frequencies[indexes]
            powers = powers[indexes]
            indexes = np.argsort(frequencies)
            frequencies = frequencies[indexes]
            powers = powers[indexes]
            for i in range(len(frequencies)):
                logger.info(sdr.tools.format_frequency_power(int(frequencies[i]), float(powers[i])))
            if 1 < print_best_frequencies:
                logger.info("-" * 80)

        if kwargs["disable_recording"]:
            return False
        else:
            return self.__recoder.record(data, _time, frequencies, powers, _range, **kwargs)

    def analyse(self, **kwargs):
        (data, _time, _range) = self.__queue.get()
        return self.__analyse(data, _time, _range, **kwargs)
