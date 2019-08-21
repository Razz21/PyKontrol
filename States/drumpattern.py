import midi_ports as mp
import padKontrol as pk
from collections import deque
from decorators import *
from itertools import count
from random import gauss


class Instrument:
    """Instrument class for sequencer

    Arguments:
        note: midi pitch value
        strokes: (optional) velocities of each stroke, default [None]*16
    Raises:
        TypeError: Strokes must be list/tuple with values None or 0-127

    """

    id_iter = count(1)  # start with 1

    def __init__(self, note, **kwargs):
        self.note = note  # triggered note # TODO unique value for channel
        self._strokes = kwargs.get(
            "strokes", [None] * 16
        )  # initialize grid with 0 velocity per step
        self._position = 0
        self.max_length = 16
        self.id = next(self.id_iter)

    @property
    def strokes(self):
        return self._strokes

    @strokes.setter
    def strokes(self, pattern: list) -> None:
        if not isinstance(pattern, (list, tuple)):
            raise TypeError("Strokes must be a list")
        if len(pattern) > self.max_length:
            self._strokes = pattern[: self.max_length]
        elif len(pattern) < self.max_length:
            self._strokes = pattern + [0] * (self.max_length - len(pattern))

    def __str__(self):
        return f"Trigger note {self.note}"

    def __iter__(self):
        return self

    def __next__(self):
        """Infinite cycle iterator for strokes

        Returns:
            tuple  -- instrument note and current stroke velocity
        """
        velocity = self.strokes[self._position]
        self._position += 1
        if self._position >= len(self.strokes):
            self._position = 0
        return (self.note, velocity)

    def reset(self):
        """Reset current stroke iterator position
        """
        self._position = 0

    def add_step(self, step: int, velocity: int) -> None:
        """Change velocity of step

        Arguments:
            step {int} -- index of existing step
            velocity {int} -- new velocity value

        Returns:
            None
        """
        if 0 <= step < len(self.strokes):
            velocity = max(0, min(velocity, 127))
            self.strokes[stroke] = velocity

    def remove_step(self, step: int) -> None:
        """Remove step velocity value

        Arguments:
            step {int} -- index of existing step

        Returns:
            None
        """
        step = max(0, min(step, len(self._strokes) - 1))
        self._strokes[step] = 0

    def add_length(self):
        """Increase strokes lengts (max-16)
        """
        if len(self.strokes) < 16:
            self.strokes += [0]

    def remove_length(self):
        """Increase strokes lengts (min-1)
        """
        if len(self.strokes) > 1:
            del self.strokes[:-1]


class Drumpattern(object):
    """Container and iterator for a multi-track step sequence."""

    def __init__(self, humanize=0):
        self.instruments = deque()
        self.humanize = humanize
        self.steps = 16
        self.step = 0
        self._notes = {}
        self.curent_instrument = None

    def reset(self):
        self.step = 0
        for instrument in self.instruments:
            instrument.reset()

    def initialize(self):
        for n in range(4):
            i = Instrument(note=36 + n)
            self.instruments.append(i)

    def playstep(self, bpm, channel=1):
        for inst in self.instruments:
            note, velocity = next(inst)

            if velocity is not None:
                if self._notes.get(note):
                    mp.send_midi(
                        dict(type="note_on", channel=channel, note=note, velocity=0)
                    )
                    self._notes[note] = 0
                if velocity > 0:
                    if self.humanize:
                        velocity += int(round(gauss(0, velocity * self.humanize)))
                    mp.send_midi(
                        dict(
                            type="note_on",
                            channel=channel,
                            note=note,
                            velocity=max(1, velocity),
                        )
                    )
                    self._notes[note] = velocity

        self.step += 1
        if self.step >= self.steps:
            self.step = 0
        self.current_instrument_seq(bpm)

    @press_light
    @action_on_press(False)
    def next_instrument(self, sysEx):
        """switch active instrument to next object

        Arguments:
            sysEx message
        """
        self.instruments.rotate(-1)
        self.load_current_instrument()

    @press_light
    @action_on_press(False)
    def prev_instrument(self, sysEx):
        """switch active instrument to previous object

        Arguments:
            sysEx message
        """
        self.instruments.rotate(1)
        self.load_current_instrument()

    @action_on_press(False)
    def handle_step(self, sysEx):
        """light on active steps

        Arguments:
            sysEx message
        """
        strokes = self.curent_instrument.strokes
        if sysEx.control < len(strokes):
            if strokes[sysEx.control]:
                strokes[sysEx.control] = 0
                mp.light_off(sysEx.control)
            else:
                strokes[sysEx.control] = sysEx.data
                mp.light_on(sysEx.control)
        else:
            mp.light_flash(sysEx.control, 0.1)

    def load_current_instrument(self):
        """load first instrument from deque
        """
        self.curent_instrument = self.instruments[0]
        inst = self.curent_instrument
        strokes = inst.strokes

        mp.group_light_off(pk.ALL_PADS)
        for idx, s in enumerate(strokes):
            if s:
                mp.light_on(idx)

        mp.led(inst.id)

    def current_instrument_seq(self, bpm):
        """flash pad on active step

        Arguments:
            bpm {int} -- sequence tempo
        """
        inst = self.curent_instrument
        tick = bpm / 960  # 16th grid
        val = (tick - 9) / 270
        mp.light_flash(inst._position, 0.125)
