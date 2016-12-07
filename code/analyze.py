import math
import numpy
import colorsys
import random


class Marker:
    def __init__(self, pos, height, color):
        self.pos = pos
        self.height = height
        self.color = color


def find_valleys(cross):  # may use set max instead of max_amp
    set_max = 0.0
    for c in cross:
        set_max = c[2] if c[2] > set_max else set_max

    valleys = []
    # isolate dramatic valleys
    last_peak = [0, 0]
    for i in range(len(cross)-1):
        # iterate until a valley is found

        if cross[i][2] > last_peak[1]:
            last_peak[1] = cross[i][2]
            last_peak[0] = i
        else:
            if cross[i][2] < cross[i+1][2]:
                next_peak = [0, 0]
                for j in range(i, len(cross)-1):
                    if cross[j][2] > next_peak[1]:
                        next_peak[1] = cross[j][2]
                        next_peak[0] = j
                    if cross[j+1][2] < cross[j][2]:
                        break

                thresh = 0.2

                last_delta = (last_peak[1] - cross[i][2]) / set_max
                next_delta = (next_peak[1] - cross[i][2]) / set_max
                if last_delta > thresh and next_delta > thresh:
                    # is valley
                    last_peak = [0, 0]
                    valleys += [i]
    return valleys


def analyze(data, start, end):
    markers = []
    # find max amplitude
    max_amp = 0.0
    max_pos = 0
    for i in range(start, end):
        s = math.fabs(data[i])
        if s > max_amp:
            max_amp = s
            max_pos = i

    # find zero crossings
    cross = []
    amp_tol = 0.015
    peak_amp = 0.0
    for i in range(start, end-1):
        # determine if sign change since last
        peak_amp = math.fabs(data[i]) if math.fabs(data[i]) > peak_amp else peak_amp

        if numpy.sign(data[i]) != numpy.sign(data[i+1]):
            # see if loud enough
            if (peak_amp / max_amp) > amp_tol:
                cross += [(i, numpy.sign(data[i+1]), peak_amp)]
            peak_amp = 0.0

    # find everage crossing delta and ensure alternating
    tol = 0.4
    chunks = []
    current_chunk = []
    current_delta = -1.0
    chunk_error = 0
    i = 0
    while i < (len(cross) - 1):
        if cross[i][1] != cross[i+1][1]:
            delta = cross[i+1][0] - cross[i][0]
            if current_delta == -1.0:
                current_delta = delta
                current_chunk += [cross[i]]
                i += 1
            else:
                avg_delta = current_delta / float(len(current_chunk))
                error = math.fabs((delta - avg_delta) / float(avg_delta))
                amp_a, amp_b = cross[i][2], cross[i+1][2]
                adapt_tol = (1.0 - math.fabs((amp_a - amp_b) / max(amp_a, amp_b))) * tol
                if error < adapt_tol:
                    current_chunk += [cross[i]]
                    current_delta += delta
                    i += 1
                else:
                    if len(current_chunk) != 0:
                        chunks += [(current_chunk, chunk_error)]
                        chunk_error = error
                        current_chunk = []
                        current_delta = -1.0
        else:
            i += 1
            if len(current_chunk) != 0:
                chunks += [(current_chunk, chunk_error)]
                chunk_error = -1.0
                current_chunk = []
                current_delta = -1.0

    if len(current_chunk) != 0:
        chunks += [(current_chunk, chunk_error)]

    final_chunks = []
    for chunk in chunks:
        valleys = find_valleys(chunk[0])
        if len(valleys) == 0:
            final_chunks += [chunk]
        else:
            last = 0
            for valley in valleys:
                final_chunks += [(chunk[0][last:valley], 0.5)] # find a better solution for error
                last = valley
            final_chunks += [(chunk[0][last:], 0.5)]

    hu = 0.0
    hu_step = 0.3
    for chunk in final_chunks:
        hu += hu_step*chunk[1]
        r, g, b, = 0.0, 0.0, 0.0
        if chunk[0][0][0] < max_pos < chunk[0][-1][0]:
            r, g, b = colorsys.hsv_to_rgb(hu, 1.0, 1.0)
        else:
            r, g, b = colorsys.hsv_to_rgb(hu, 1.0, 0.2)

        for c in chunk[0]:
            m = Marker(c[0], 0, (r, g, b))
            markers += [m]

    return markers
