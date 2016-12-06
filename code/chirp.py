from scipy.signal import butter, lfilter
import numpy
import wave
import struct
import math

import threading
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

in_audio = wave.open('4_20_a.wav', 'rb')

IN_SAMPLEWIDTH = in_audio.getsampwidth()
IN_FRAMERATE = in_audio.getframerate()
IN_NFRAMES = in_audio.getnframes()


data = in_audio.readframes(IN_NFRAMES)
raw = struct.unpack('<%dh' % IN_NFRAMES, data)

# normalize
max_s = 0.0
min_s = 0.0
for s in raw:
    min_s = s if s < min_s else min_s
    max_s = s if s > max_s else max_s

samples = numpy.array(raw)

amplify = (65535.0/2) / max(math.fabs(min_s), max_s)
samples *= amplify

# band pass
filtered = butter_bandpass_filter(samples, 3000, 5000, IN_FRAMERATE)


wave_display = data_display.WaveformDisplay(filtered)
display = data_display.Display(600, 300, wave_display, IN_FRAMERATE)


loop = threading.Thread(target=display.start_window)
loop.start()