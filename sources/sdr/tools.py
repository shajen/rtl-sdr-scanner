#!/usr/bin/python3


def format_frequnecy(frequency):
    if frequency >= 1000000:
        return "%.4f MHz" % (frequency / 1000000)
    elif frequency >= 1000:
        return "%.1f kHz" % (frequency / 1000)
    else:
        return "%d Hz" % frequency


def format_frequnecies(frequencies):
    return ", ".join([format_frequnecy(f) for f in frequencies])
