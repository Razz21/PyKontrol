from States.baseState import State
import padKontrol as pk
import time
import utils
from collections import deque
from rtmidi.midiconstants import (
    ALL_SOUND_OFF,
    BANK_SELECT_LSB,
    BANK_SELECT_MSB,
    CHANNEL_VOLUME,
    CONTROL_CHANGE,
    NOTE_ON,
    NOTE_OFF,
    PROGRAM_CHANGE,
)
import string
import midi_ports as mp
from decorators import *


class FreeState(State):
    _scales = deque(
        [
            ("Chromatic", [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], []),
            (
                "MAjor",
                [2, 2, 1, 2, 2, 2, 1],
                [
                    "Ionian",
                    "Dorian",
                    "Phrygian",
                    "Lydian",
                    "MIxolydian",
                    "AEolian",
                    "Locrian",
                ],
            ),
            ("NAtural minor", [2, 1, 2, 2, 1, 2, 2], []),
            ("HArmonic minor", [2, 1, 2, 2, 1, 3, 1], []),
            ("Usr", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], []),  # TODO create own scale
        ]
    )

    state_name = "frE"
    ordered = [
        12,
        13,
        14,
        15,
        8,
        9,
        10,
        11,
        4,
        5,
        6,
        7,
        0,
        1,
        2,
        3,
    ]  # pad order left-right / down-up

    def __init__(self,):
        super().__init__()
        self.hotkeys = set()
        self._LOCAL_COMBINATIONS = {
            frozenset([pk.BUTTON_PEDAL, pk.ROTARY_KNOB]): self.change_mode,
            frozenset([pk.BUTTON_FLAM, pk.ROTARY_KNOB]): self.transpose_12,
            # frozenset([pk.BUTTON_PAD]): self.pitch_bend,
        }
        self.channel = 1
        self._transpose = 0
        self.scale = None
        self.led_text = None
        self.mode = 0
        self.base_note = 36

    @property
    def transpose(self):
        return self._transpose

    @transpose.setter
    def transpose(self, val):
        self._transpose = max(min(127, val), -36)

    def handle_pad(self, sysEx):
        self.play_note(sysEx)

    def handle_button(self, sysEx):
        # print(sysEx)
        if sysEx.control == pk.BUTTON_HOLD:
            self.handle_transpose(sysEx, 1)
        elif sysEx.control == pk.BUTTON_ROLL:
            self.handle_transpose(sysEx, -1)
        elif sysEx.control == pk.BUTTON_FLAM:
            self.show_note(sysEx)
        elif sysEx.control == pk.BUTTON_PAD:
            self.handle_xy_pad(sysEx)

    def handle_knob(self, sysEx):
        pass

    def handle_rotary(self, sysEx):
        if sysEx.data == 1:
            self._scales.rotate(-1)
        else:
            self._scales.rotate(1)
        self.mode = 0
        self.load_scale()

    def handle_xy_pad(self, sysEx):
        # pitch bend on x
        if sysEx.state == 1 and sysEx.data:
            # 1 semitone pitch bend
            pitch = round(275 / 128 * sysEx.data[1] - 137)

            mp.send_midi(dict(type="pitchwheel", pitch=pitch))
        elif sysEx.state == 0:
            mp.send_midi(dict(type="pitchwheel", pitch=0))

    def load_scale(self):
        """
        Change pattern and load prepared scale.
        """
        name, pattern, modes = self._scales[0]
        self.scale = utils.scale_to_16(pattern, self.mode)
        if self.mode:
            name = modes[self.mode]
        self.led_text = name
        mp.led('@#2', pk.LED_STATE_BLINK)
        # mp.led_reset()


    def change_mode(self, sysEx):
        """
        Change mode of current scale if exists.
        """
        scale_modes = len(self._scales[0][2]) or None
        if scale_modes:
            if sysEx.data == 1:
                self.mode += 1
            else:
                self.mode -= 1

            if self.mode < 0:
                self.mode = scale_modes - 1
            elif self.mode >= scale_modes:
                self.mode = 0
            self.load_scale()

    @press_light
    def play_note(self, sysEx):
        """
        Play notes with pads.
        """
        pad = self.ordered[sysEx.control]
        scale = self.scale
        note = self.base_note + scale[pad]
        mp.send_midi(
            dict(type=sysEx.state, channel=self.channel, note=note, velocity=sysEx.data)
        )

    @press_light
    @action_on_press(True, "led_text")  # reset led on button release
    def handle_transpose(self, sysEx, steps):
        """
        Transpose base note ± 1 semitone.
        """
        self.transpose += steps
        self.base_note = 36 + self.transpose
        note_name = utils.pitch_to_note(self.base_note)
        mp.led(note_name)

    def load_state(self):
        self.clear_state()

    def clear_state(self):
        """
        Initialize state variables.
        """
        self.load_scale()
        self.channel = 1
        self.base_note = 36
        self._transpose = 0

    @press_light
    @action_on_press(True, "led_text")
    def show_note(self, sysEx):
        """
        Display current note pitch.
        """
        note_name = utils.pitch_to_note(self.base_note)
        mp.led(note_name)

    def transpose_12(self, sysEx):
        """
        Transpose base note ± 12 semitones.
        """
        if sysEx.data == 1:
            self.transpose += 12
        else:
            self.transpose -= 12

        self.base_note = 36 + self.transpose
        note_name = utils.pitch_to_note(self.base_note)
        mp.led(note_name)
