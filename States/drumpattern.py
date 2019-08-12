import midi_ports as mp
import padKontrol as pk
from collections import deque
from decorators import *


class Instrument:
    """
    Instrument class for sequencer
    Attributes:
      - unique sequence length
      - specify independent steps
      - convert to string drumpattern
    Future:
      - read / save midi files #todo
    """

    __slots__ = ("note", "strokes", "position", "max_length")

    def __init__(self, note, **kwargs):
        self.note = note  # triggered note # TODO unique value for channel
        self._strokes = kwargs.get(
            "strokes", [None] * 16
        )  # initialize grid with 0 velocity per step
        self._position = 0
        self.max_length = 16

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
        stroke = self.strokes[self._position]
        self._position += 1
        if self._position >= len(self.strokes):
            self._position = 0
        return (self.note, stroke)

    def reset(self):
        self._position = 0

    def add_step(self, step: int, velocity: int) -> None:
        step = max(0, min(step, len(self._strokes) - 1))
        velocity = max(0, min(velocity, 127))
        self._strokes[step] = velocity

    def remove_step(self, step: int) -> None:
        step = max(0, min(step, len(self._strokes) - 1))
        self._strokes[step] = 0  # not throw error

    def add_length(self):
        if len(self.strokes) < 16:
            self.strokes += [0]

    def remove_length(self):
        if len(self.strokes) > 1:
            del self.strokes[:-1]

    def change_velocity(self, stroke: int, val: int):
        if 0 <= stroke < len(self.strokes):
            val = max(0, min(val, 127))
            self.strokes[stroke] = val


class Drumpattern(object):
    """Container and iterator for a multi-track step sequence."""

    _curr_instrument_idx = 1

    def __init__(self, kit=0, humanize=0):
        self.instruments = deque()
        self.kit = kit
        self.humanize = humanize
        self.steps = 16
        self.step = 0
        self._notes = {}
        self.curent_instrument = None

    def __len__(self):
        return len(self.instruments)

    def reset(self):
        self.step = 0
        for instrument in self.instruments:
            instrument["current_step"] = 0

    def initialize(self):
        for n in range(4):
            i = {"note": 36 + n, "strokes": [0] * 16, "current_step": 0}
            self.instruments.append(i)

    def playstep(self, channel=9):
        for idx, inst in enumerate(self.instruments):
            note, strokes, current_step = inst.values()
            velocity = strokes[current_step]
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

            current_step += 1
            if current_step >= len(strokes):
                current_step = 0

            self.instruments[idx]["current_step"] = current_step

        self.step += 1
        if self.step >= self.steps:
            self.step = 0
        self.current_instrument_seq()

    def change_curr_idx(self, val):
        self._curr_instrument_idx += val
        if self._curr_instrument_idx > len(self.instruments):
            self._curr_instrument_idx = 1

        elif self._curr_instrument_idx < 1:
            self._curr_instrument_idx = len(self.instruments)

    @press_light
    @action_on_press(False)
    def next_instrument(self, sysEx):
        self.instruments.rotate(-1)
        self.change_curr_idx(1)
        self.load_current_instrument()

    @press_light
    @action_on_press(False)
    def prev_instrument(self, sysEx):
        self.instruments.rotate(1)
        self.change_curr_idx(-1)
        self.load_current_instrument()

    @action_on_press(False)
    def handle_step(self, sysEx):
        strokes = self.curent_instrument["strokes"]
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
        self.curent_instrument = self.instruments[0]
        inst = self.curent_instrument
        strokes = inst["strokes"]
        # print(strokes)
        mp.group_light_off(pk.ALL_PADS)
        for idx, s in enumerate(strokes):
            if s:
                mp.light_on(idx)

        mp.led(self._curr_instrument_idx)

    def current_instrument_seq(self):
        inst = self.curent_instrument
        note, strokes, current_step = inst.values()
        # print(current_step, strokes[current_step])
        # if current_step >= len(strokes):
        #     current_step = 0
        mp.light_flash(current_step, 0.1)

    # def strokes_to_active(self, strokes: list) -> dict:
    #     todo sysex group messages
    #     # create dict of active pads for padkontrol module
    #     res = {k: True if strokes[k] else False for k in range(len(strokes))}
    #     return res
