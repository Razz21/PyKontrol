import asyncio

# class Singleton(type):
#     _instances = {}

#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]


class Stoppable:
    def __init__(self, coro):
        self._coro_iter = coro.__await__()
        self._stopped = None

    def __await__(self):
        while True:
            while self._stopped:
                print("awaiting stopped")
                yield from self._stopped.__await__()
            try:
                v = next(self._coro_iter)
            except StopIteration as e:
                return v
            yield v

    def stop(self):
        loop = asyncio.get_event_loop()
        self._stopped = loop.create_future()

    def start(self):
        if self._stopped is not None:
            self._stopped.set_result(None)
            self._stopped = None


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


# def trigger(note_on, note_off, note=60, channel=0, trig=0.005):
#     port.send(note_on)
#     time.sleep(trig)
#     port.send(note_off)


octaves = ["-"] + list(range(10))  # must return only 1 character
names = ["C ", "C#", "d ", "d#", "E ", "F ", "F#", "G ", "G#", "A ", "A#", "b "]


def pitch_to_note(pitch):
    pitch = max(min(pitch, 127), 0)  # range 0-127
    octave = pitch // 12
    n = pitch % 12
    return names[n] + str(octaves[octave])
