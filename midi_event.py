from collections import namedtuple


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


class SysexEvent(namedtuple("Sysex", ["type", "control", "state", "data"])):
    """Container for precessed sysEx messages from PK device.

    Arguments:
        type {string} -- group representation of controller (button / knob / pad),
        control {int} -- parameter description,
        state {int/string} -- event type (for buttons/pads: pressed or released , knobs: 1),
        data {int/tuple} (optional) -- transmitted value/s.

    Returns:
        namedtuple object
    """

    __slots__ = ()

    def __new__(cls, type, control, state=1, data=None):
        return super(SysexEvent, cls).__new__(cls, type, control, state, data)

    def __eq__(self, other):
        return self.control == other.control and self.state == other.state

    def __lt__(self, other):
        return self.control == other.control and self.data < other.data

    def __le__(self, other):
        return self.control == other.control and self.data <= other.data

    def __gt__(self, other):
        return self.control == other.control and self.data > other.data

    def __ge__(self, other):
        return self.control == other.control and self.data >= other.data
