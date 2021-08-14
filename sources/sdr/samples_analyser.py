#!/usr/bin/python3

import matplotlib.mlab
import numpy as np
import logging
import sdr.tools
import sdr.samples_decoder
import scipy.signal as signal


class SamplesAnalyser:
    def __init__(self, queue, **kwargs):
        self.__queue = queue
        self.__samplesDecoder = sdr.samples_decoder.SamplesDecoder()

    def __get_frequency_power(self, data, start, stop, **kwargs):
        fft = kwargs["fft"]
        bandwidth = kwargs["bandwidth"]
        frequency = (stop + start) // 2
        [powers, frequencies] = matplotlib.mlab.psd(data, NFFT=fft, Fs=bandwidth)
        return (frequencies + frequency), np.log10(powers)

    def __filter_frequencies(self, frequencies, **kwargs):
        ignored_frequencies_ranges = kwargs["ignored_frequencies_ranges"]
        is_ok = lambda frequency: not any(_range["start"] <= frequency and frequency <= _range["stop"] for _range in ignored_frequencies_ranges)
        mask = [is_ok(frequency) for frequency in frequencies]
        return np.arange(len(frequencies))[mask]

    def __analyse(self, data, start, stop, **kwargs):
        logger = logging.getLogger("sdr")
        print_best_frequencies = kwargs["print_best_frequencies"]
        disable_recording = kwargs["disable_recording"]

        frequencies, powers = self.__get_frequency_power(data, start, stop, **kwargs)

        frequencies_index = signal.find_peaks(powers, width=kwargs["peak_width"])[0]
        frequencies = frequencies[frequencies_index]
        powers = powers[frequencies_index]

        frequencies_index = self.__filter_frequencies(frequencies, **kwargs)
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
                logger.debug(sdr.tools.format_frequency_power(int(frequencies[i]), float(powers[i])))
            if 1 < print_best_frequencies:
                logger.debug("-" * 80)

        if disable_recording:
            return False
        else:
            return self.__samplesDecoder.decode(data, frequencies, powers, start, stop, **kwargs)

    def analyse(self, **kwargs):
        (data, start, stop) = self.__queue.get()
        return self.__analyse(data, start, stop, **kwargs)
