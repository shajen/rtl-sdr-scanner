#!/usr/bin/python3


def colored(string, color=None, background=None, attrs=None):
    try:
        import termcolor

        return termcolor.colored(string, color, background)
    except:
        return string


def format_frequnecy(frequency):
    if frequency == 0:
        return "0 MHz"
    elif frequency >= 1000000:
        return "{:,.2f} MHz".format(frequency / 1000)
    elif frequency >= 1000:
        return "%.1f kHz" % (frequency / 1000)
    else:
        return "%d Hz" % frequency


def format_frequnecy_power(frequency, power):
    return "frequnecy: %14s, power: %5.2f dB %s" % (format_frequnecy(frequency), power, format_power(power))


def format_frequnecies(frequencies):
    return ", ".join([format_frequnecy(f) for f in frequencies])


def format_frequnecy_range(start, stop, step=0):
    if step == 0:
        return "%s - %s" % (format_frequnecy(start), format_frequnecy(stop))
    else:
        return "%s - %s, step: %8s" % (format_frequnecy(start), format_frequnecy(stop), format_frequnecy(step))


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
    return format_bar(value, min=0, max=20, length=40)
