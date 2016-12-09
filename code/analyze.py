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
    debug = []

    set_max = 0.0
    for c in cross:
        set_max = c[2] if c[2] > set_max else set_max

    valleys = []

    for i in range(1, len(cross)-1):
        if cross[i-1][2] > cross[i][2] < cross[i+1][2]:
            # find left_peak
            # find right_peak
            left_peak = ()
            right_peak = ()

            for p in range(i, 0, -1):
                slope = (cross[p-1][2] - cross[p][2]) / float(cross[p][0] - cross[p-1][0])
                if slope > -40.0:
                    if slope > 0.0:
                        left_peak = cross[p-1]
                else:
                    break

            for p in range(i, len(cross)-1):
                slope = (cross[p+1][2] - cross[p][2]) / float(cross[p+1][0] - cross[p][0])
                if slope > -40.0:
                    if slope > 0.0:
                        right_peak = cross[p+1]
                else:
                    break

            left_delta = left_peak[2] - cross[i][2]
            right_delta = right_peak[2] - cross[i][2]

            if left_delta > 1000.0 and right_delta > 10000.0:
                # print(left_delta, right_delta)
                debug += [Marker(cross[i][0], cross[i][2], (0.5, 0.0, 0.5))]
                debug += [Marker(left_peak[0], left_peak[2], (0.0, 0.7, 0.0))]
                debug += [Marker(right_peak[0], right_peak[2], (0.0, 0.0, 0.7))]
                valleys += [i]

    return valleys, debug


def find_valleys2(cross):  # may use set max instead of max_amp
    debug = []

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
                for j in range(i, len(cross)):
                    if cross[j][2] > next_peak[1]:
                        next_peak[1] = cross[j][2]
                        next_peak[0] = j
                    else:
                        break

                thresh = 0.05

                last_dist = i - last_peak[0]
                next_dist = min(next_peak[0] - i, 12) / 2.0

                last_delta = ((last_peak[1] - cross[i][2]) / float(last_dist)) / 32768.0  # / set_max
                next_delta = ((next_peak[1] - cross[i][2]) / float(next_dist)) / 32768.0  # / set_max
                if next_delta > thresh and last_dist > 1:  # or last_delta > thresh:
                    # debug
                    print("PEAK: %0.5f  %0.5f" % (last_delta, next_delta))
                    debug += [Marker(cross[i][0], cross[i][2], (1.0, 0.0, 1.0))]
                    debug += [Marker(cross[last_peak[0]][0], cross[last_peak[0]][2], (0.0, 1.0, 0.0))]
                    debug += [Marker(cross[next_peak[0]][0], cross[next_peak[0]][2], (0.0, 0.0, 1.0))]

                    # is valley
                    valleys += [i]
                else:
                    # debug
                    print("peak: %0.5f  %0.5f" % (last_delta, next_delta))
                    debug += [Marker(cross[i][0], cross[i][2], (0.3, 0.0, 0.3))]
                    debug += [Marker(cross[last_peak[0]][0], cross[last_peak[0]][2], (0.0, 0.3, 0.0))]
                    debug += [Marker(cross[next_peak[0]][0], cross[next_peak[0]][2], (0.0, 0.0, 0.3))]

                # test
                last_peak = [0, 0]

    return valleys, debug


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
                # debug
                m = Marker(i, peak_amp, (0.0, 0.4, 0.4))
                markers += [m]
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
        valleys, debug = find_valleys(chunk[0])
        markers += debug
        if len(valleys) == 0:
            final_chunks += [chunk]
        else:
            last = 0
            for valley in valleys:
                final_chunks += [(chunk[0][last:valley], 0.5)]  # find a better solution for error
                last = valley
            final_chunks += [(chunk[0][last:], 0.5)]

    start = 0.0

    hu = 0.0
    hu_step = 0.3
    for chunk in final_chunks:
        hu += hu_step*chunk[1]
        r, g, b, = 0.0, 0.0, 0.0
        if chunk[0][0][0] < max_pos < chunk[0][-1][0]:
            start = chunk[0][0][0]
            r, g, b = colorsys.hsv_to_rgb(hu, 1.0, 1.0)
        else:
            r, g, b = colorsys.hsv_to_rgb(hu, 1.0, 0.2)

        for c in chunk[0]:
            m = Marker(c[0], 0, (r, g, b))
            markers += [m]

    return start, markers
