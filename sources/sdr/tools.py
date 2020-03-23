#!/usr/bin/python3


def colored(string, color=None, background=None, attrs=None):
    try:
        import termcolor

        return termcolor.colored(string, color, background)
    except:
        return string


def format_frequnecy(frequency):
    if frequency >= 1000000:
        return "%.4f MHz" % (frequency / 1000000)
    elif frequency >= 1000:
        return "%.1f kHz" % (frequency / 1000)
    else:
        return "%d Hz" % frequency


def format_frequnecies(frequencies):
    return ", ".join([format_frequnecy(f) for f in frequencies])


def format_bar(value, **kwargs):
    min_value = kwargs.get("min", 0)
    max_value = kwargs.get("max", 100)
    length = kwargs.get("length", 80)

    if value <= min_value:
        n = 0
    elif max_value <= value:
        n = length
    else:
        single = (max_value - min_value) / length
        n = round((value - min_value) / single)
    return "#" * n + "_" * (length - n)


def format_power(value):
    return format_bar(value, min=0, max=40, length=40)
