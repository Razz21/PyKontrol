import asyncio
from math import ceil
from itertools import accumulate, cycle, islice
from collections import deque

# class Stoppable:
#     def __init__(self, coro):
#         self._coro_iter = coro.__await__()
#         self._stopped = None

#     def __await__(self):
#         while True:
#             while self._stopped:
#                 print("awaiting stopped")
#                 yield from self._stopped.__await__()
#             try:
#                 v = next(self._coro_iter)
#             except StopIteration as e:
#                 return v
#             yield v

#     def stop(self):
#         loop = asyncio.get_event_loop()
#         self._stopped = loop.create_future()

#     def start(self):
#         if self._stopped is not None:
#             self._stopped.set_result(None)
#             self._stopped = None


def keep_in_range(n, minn, maxn):
    return max(min(maxn, n), minn)


def get_piano_notes(transpose=12):
    """
    default range - C2-E3b (or C3-E4b in American English)
    default range in midi - 48-63
    transpose move range +- 4 notes
    """
    transpose = keep_in_range(transpose, 0, 28)  # full range 0-127
    bottom_note = max(0, 4 * transpose)  # left bottom
    last_note = min(127, bottom_note + 15)  # right upper
    return bottom_note, last_note

octaves = ["-"] + list(range(10))  # must return only 1 character
names = ["C ", "Ch", "d ", "dh", "E ", "F ", "Fh", "G ", "Gh", "A ", "Ah", "b "]


def pitch_to_note(pitch):
    pitch = max(min(pitch, 127), 0)  # range 0-127
    octave = pitch // 12
    n = pitch % 12
    return names[n] + str(octaves[octave])


def scale_to_mode(scale, transpose=0):
    """Create mode of given scale

    Arguments:
        scale {list} -- scale scheme

    Keyword Arguments:
        transpose {int} -- transpose value (default: {0})

    Returns:
        list -- scale scheme in mode

    Caution: these calculation are computational expensive
    """
    #  find mode scheme based on original scale
    l = scale[transpose:]
    #  create complete 16-elements list of steps
    i = ceil((16 - len(l)) / 12)
    l += scale * i
    l = list(accumulate(l))
    n = l[0]
    l = list(map(lambda x: x - n, l))

    return l[:16]


def scale_to_pattern(scale):
    # find relative next note pattern from 12 keys scale scheme
    pattern = [t - s for s, t in zip(scale, scale[1:])]


def scale_to_16(scale, mode=0, base=0, length=16):
    """Create x-length step cycled scale pattern

    Arguments:
        scale {list} -- distance in semitones between consecutive scale notes

    Keyword Arguments:
        mode {int} -- apply mode of the scale by rotating scale list elements
        base {int} -- base note realtive pitch (default: {0})
        length {int} -- length of result pattern (default: {16})

    Returns:
        res_acc {list} -- accumulated distance of consecutive scale notes from base note
    """
    pattern = deque(scale)
    pattern.rotate(mode)
    result = deque(islice(cycle(pattern), (length - 1)))

    result.appendleft(base)

    res_acc = list(accumulate(result))
    return res_acc