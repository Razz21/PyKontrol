import time
import pkconstants as const


class MidiEvent(object):
    """Container for a MIDI message and a timing tick.

    Bascially like a two-item named tuple, but we overwrite the comparison
    operators, so that they (except when testing for equality) use only the
    timing ticks.

    """

    __slots__ = ("tick", "message")

    def __init__(self, tick, message):
        self.tick = tick
        self.message = message

    def __repr__(self):
        return "@ %05i %r" % (self.tick, self.message)

    def __eq__(self, other):
        return self.tick == other.tick and self.message == other.message

    def __lt__(self, other):
        return self.tick < other.tick

    def __le__(self, other):
        return self.tick <= other.tick

    def __gt__(self, other):
        return self.tick > other.tick

    def __ge__(self, other):
        return self.tick >= other.tick
