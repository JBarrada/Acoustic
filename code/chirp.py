from scipy.signal import butter, lfilter
import numpy
import wave
import struct
import math
import random
import colorsys
import threading

import analyze
import data_display


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def setup(samples, fs, normalize=True, band_pass=True):
    if normalize:
        # normalize
        max_s = 0.0
        min_s = 0.0
        for s in samples:
            min_s = s if s < min_s else min_s
            max_s = s if s > max_s else max_s

        samples = numpy.array(samples)

        amplify = (65535.0/2) / max(math.fabs(min_s), max_s)
        samples *= amplify

    if band_pass:
        # band pass
        samples = butter_bandpass_filter(samples, 3000, 5000, fs)

    return samples


batch = True

if batch:
    files = ["2_10_a", "2_10_b", "2_10_c"]
    # files += ["3_15_a", "3_15_b", "3_15_c"]
    # files += ["4_20_a", "4_20_b", "4_20_c"]

    for f_name in files:
        in_audio = wave.open('samples\\%s.wav' % f_name, 'rb')

        IN_SAMPLEWIDTH = in_audio.getsampwidth()
        IN_FRAMERATE = in_audio.getframerate()
        IN_NFRAMES = in_audio.getnframes()

        data = in_audio.readframes(IN_NFRAMES)
        raw = struct.unpack('<%dh' % IN_NFRAMES, data)

        filtered = setup(raw, IN_FRAMERATE)

        f = open("samples\\%s.txt" % f_name, "r")
        template = f.readlines()
        f.close()

        print(f_name)
        for line in template:
            keys = map(int, line.split(","))
            start, markers = analyze.analyze(filtered, keys[0], keys[2])

            error = (math.fabs(keys[1] - start) / float(IN_FRAMERATE)) * 1000.0
            print("ERR: %0.3fmS" % error)

        print("")

else:
    in_audio = wave.open('samples\\2_10_a.wav', 'rb')

    IN_SAMPLEWIDTH = in_audio.getsampwidth()
    IN_FRAMERATE = in_audio.getframerate()
    IN_NFRAMES = in_audio.getnframes()

    data = in_audio.readframes(IN_NFRAMES)
    raw = struct.unpack('<%dh' % IN_NFRAMES, data)

    filtered = setup(raw, IN_FRAMERATE)

    wave_display = data_display.WaveformDisplay(filtered)
    display = data_display.Display(600, 300, wave_display, IN_FRAMERATE)
    loop = threading.Thread(target=display.start_window)
    loop.start()
